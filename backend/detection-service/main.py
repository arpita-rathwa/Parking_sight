import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from detector.model import DetectionModel
from detector.types import CameraConfig, DetectionResult, VehicleType
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pipeline.batcher import BatchInferencePipeline
from pydantic import BaseModel
from sqlalchemy.orm import Session
from stream.manager import StreamManager

from shared.auth.jwt import require_role
from shared.config.settings import settings
from shared.kafka.producer import producer
from shared.kafka.topics import KAFKA_TOPICS
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.database import Base, get_db, get_engine
from shared.models.violations import Violation

app = FastAPI(title="detection-service", version="1.0.0")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(StructuredLoggingMiddleware)

model: DetectionModel | None = None
stream_manager: StreamManager = StreamManager()
pipeline: BatchInferencePipeline | None = None


@app.on_event("startup")
def on_startup():
    global model, pipeline
    Base.metadata.create_all(bind=get_engine())
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

    close_session = False
    if db is None:
        from shared.models.database import get_session

        db = get_session()
        close_session = True

    try:
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
    finally:
        if close_session:
            db.close()

    event = {
        "violation_id": str(violation_id),
        "camera_id": camera_id,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": now.isoformat(),
        "confidence": confidence,
        "vehicle_type": vehicle_type.value,
        "violation_type": violation_type,
    }
    producer.send(KAFKA_TOPICS["violations_raw"], key=str(violation_id), value=event)
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
    detections = model.predict_single(frame)

    if not detections:
        return {
            "detections": [],
            "message": "No vehicles detected",
        }

    results = []
    for det in detections:
        vid = _publish_detection(
            camera_id=camera_id,
            vehicle_type=det.vehicle_type,
            confidence=det.confidence,
            latitude=latitude,
            longitude=longitude,
            db=db,
        )
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
