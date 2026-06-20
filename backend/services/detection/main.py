import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from detector.geometry import filter_detections_by_roi, point_in_polygon
from detector.model import DetectionModel
from detector.types import CameraConfig, DetectionResult, VehicleType
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pipeline.batcher import BatchInferencePipeline
from pydantic import BaseModel
from sqlalchemy.orm import Session
from stream.manager import StreamManager

from shared.auth.jwt import require_role
from shared.auth.routes import router as auth_router
from shared.config.settings import settings
from shared.kafka.producer import producer
from shared.kafka.topics import KAFKA_TOPICS
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.cameras import Camera
from shared.models.database import get_db
from shared.models.violations import Violation
from shared.utils.migrations import run_migrations
from shared.utils.sentry import init_sentry

logger = logging.getLogger("detection-service")

app = FastAPI(title="detection-service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(StructuredLoggingMiddleware)
app.include_router(auth_router)

model: DetectionModel | None = None
stream_manager: StreamManager = StreamManager()
pipeline: BatchInferencePipeline | None = None
_executor: asyncio.AbstractEventLoop | None = None


@app.on_event("startup")
def on_startup():
    global model, pipeline
    run_migrations()
    init_sentry(settings.SERVICE_NAME)
    model = DetectionModel(
        model_path=settings.MODEL_PATH,
        confidence_threshold=settings.DETECTION_CONFIDENCE_THRESHOLD,
        target_size=(settings.MODEL_INPUT_SIZE, settings.MODEL_INPUT_SIZE),
        half_precision=settings.ENABLE_HALF_PRECISION,
    )
    model.load()
    pipeline = BatchInferencePipeline(model=model, interval=settings.BATCH_INTERVAL)
    if settings.STREAM_CACHE_DIR:
        Path(settings.STREAM_CACHE_DIR).mkdir(parents=True, exist_ok=True)


@app.on_event("shutdown")
def on_shutdown():
    if pipeline is not None:
        pipeline.stop()
    stream_manager.stop_all()


class DetectionResponse(BaseModel):
    id: str
    camera_id: str
    timestamp: str
    latitude: float
    longitude: float
    confidence_score: float
    vehicle_type: str
    violation_type: str


class StreamStartRequest(BaseModel):
    camera_id: str
    rtsp_url: str
    latitude: float = 0.0
    longitude: float = 0.0
    frame_interval: int = 5
    roi_polygon: list[list[float]] | None = None


def _decode_image(file: UploadFile) -> np.ndarray:
    contents = file.file.read()
    arr = np.frombuffer(contents, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    return frame


def _publish_detection(
    camera_id: str,
    vehicle_type: VehicleType,
    confidence: float,
    latitude: float,
    longitude: float,
    db: Session | None = None,
) -> str:
    violation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    violation_type = "detected"
    zone_id = None

    close_session = False
    if db is None:
        from shared.models.database import get_session

        db = get_session()
        close_session = True

    try:
        from shared.models.cameras import Camera

        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if camera:
            zone_id = str(camera.zone_id)
        violation = Violation(
            id=violation_id,
            camera_id=uuid.UUID(camera_id) if camera_id else uuid.uuid4(),
            timestamp=now,
            coordinates=f"SRID=4326;POINT({longitude} {latitude})",
            confidence_score=confidence,
            vehicle_type=vehicle_type.value,
            violation_type=violation_type,
        )
        db.add(violation)
        db.commit()
    except Exception:
        logger.exception("Failed to persist violation")
        raise
    finally:
        if close_session:
            db.close()

    event = {
        "violation_id": str(violation_id),
        "camera_id": camera_id,
        "zone_id": zone_id,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": now.isoformat(),
        "confidence": confidence,
        "vehicle_type": vehicle_type.value,
        "violation_type": violation_type,
    }
    kafka_ok = producer.send(
        KAFKA_TOPICS["violations_raw"], key=str(violation_id), value=event
    )
    if not kafka_ok:
        logger.warning(
            "Kafka unreachable — violation %s persisted to DB only", violation_id
        )
    return str(violation_id)


@app.post(f"{settings.API_V1_PREFIX}/detect")
async def detect_violation(
    camera_id: str,
    latitude: float = 0.0,
    longitude: float = 0.0,
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator")),
):
    if model is None or not model.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    if file is None:
        raise HTTPException(status_code=400, detail="Image file required")

    frame = _decode_image(file)
    loop = asyncio.get_event_loop()
    detections = await loop.run_in_executor(None, model.predict_single, frame)

    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    roi = camera.roi_polygon if camera else None
    if roi:
        try:
            import json
            roi_parsed = json.loads(roi)
            h, w = frame.shape[:2]
            detections = filter_detections_by_roi(detections, roi_parsed, w, h)
        except (json.JSONDecodeError, TypeError):
            pass

    if not detections:
        return {
            "detections": [],
            "message": "No vehicles detected",
        }

    results = []
    for det in detections:
        try:
            vid = _publish_detection(
                camera_id=camera_id,
                vehicle_type=det.vehicle_type,
                confidence=det.confidence,
                latitude=latitude,
                longitude=longitude,
                db=db,
            )
        except Exception:
            logger.exception("Failed to publish detection")
            raise HTTPException(status_code=503, detail="Database unavailable")
        results.append(
            DetectionResponse(
                id=vid,
                camera_id=camera_id,
                timestamp=det.timestamp,
                latitude=latitude,
                longitude=longitude,
                confidence_score=det.confidence,
                vehicle_type=det.vehicle_type.value,
                violation_type="detected",
            )
        )

    return {"detections": results, "count": len(results)}


def _pipeline_callback(camera_id: str, detections: list[DetectionResult]) -> None:
    config = stream_manager.get_config(camera_id)
    if config and config.roi_polygon:
        detections = [
            d for d in detections
            if d.bbox and point_in_polygon(
                d.bbox.center[0], d.bbox.center[1],
                config.roi_polygon,
            )
        ]
    for det in detections:
        try:
            _publish_detection(
                camera_id=camera_id,
                vehicle_type=det.vehicle_type,
                confidence=det.confidence,
                latitude=0.0,
                longitude=0.0,
            )
        except Exception:
            pass


@app.post(f"{settings.API_V1_PREFIX}/detect/stream/start")
async def start_stream(
    req: StreamStartRequest,
    current_user=Depends(require_role("admin", "operator")),
):
    if model is None or not model.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    config = CameraConfig(
        camera_id=req.camera_id,
        rtsp_url=req.rtsp_url,
        latitude=req.latitude,
        longitude=req.longitude,
        frame_interval=req.frame_interval,
        roi_polygon=(
            [tuple(p) for p in req.roi_polygon]
            if req.roi_polygon else None
        ),
    )

    try:
        stream = stream_manager.add_camera(config)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    pipeline.set_callback(req.camera_id, _pipeline_callback)
    stream.start()
    if not pipeline.is_running:
        pipeline.start(stream_manager.get_latest_frames)

    return {
        "status": "started",
        "camera_id": req.camera_id,
        "message": f"Stream started for camera {req.camera_id}",
    }


@app.post(f"{settings.API_V1_PREFIX}/detect/stream/stop")
async def stop_stream(
    camera_id: str,
    current_user=Depends(require_role("admin", "operator")),
):
    stream_manager.stop_camera(camera_id)
    if pipeline is not None:
        pipeline.remove_callback(camera_id)
        if not pipeline.active_callbacks:
            pipeline.stop()
    return {
        "status": "stopped",
        "camera_id": camera_id,
    }


@app.get(f"{settings.API_V1_PREFIX}/detect/streams")
async def list_streams(
    current_user=Depends(require_role("admin", "operator")),
):
    return {
        "active_cameras": stream_manager.active_cameras,
        "count": stream_manager.camera_count,
        "streams": stream_manager.get_all_stats(),
    }


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {
        "status": "ok",
        "service": "detection-service",
        "model_loaded": model.is_loaded() if model else False,
        "active_streams": stream_manager.camera_count,
    }
