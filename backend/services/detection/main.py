import asyncio
import logging
import time
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock, Thread

import cv2
import numpy as np
from detector.geometry import filter_detections_by_roi, point_in_polygon
from detector.model import DetectionModel
from detector.types import CameraConfig, DetectionResult, VehicleType
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest
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
from shared.models.database import get_db, get_session
from shared.models.violations import Violation
from shared.utils.dependencies import get_dependency_report
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

_violation_buffer: deque[dict] = deque(maxlen=10000)
_buffer_lock = Lock()
_last_flush_attempt = datetime.min.replace(tzinfo=timezone.utc)

DETECTION_LATENCY = Histogram(
    "detection_inference_seconds",
    "Model inference latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
DETECTION_TOTAL = Counter("detection_total", "Total detections processed")
DETECTION_FAILURES = Counter(
    "detection_failures_total", "Total detection failures", labelnames=["reason"]
)
DETECTION_BUFFER_SIZE = Gauge("detection_buffer_size", "Current violation buffer size")
MODEL_HEALTH = Gauge("detection_model_health", "Model health (1=loaded, 0=unloaded)")
ACTIVE_STREAMS = Gauge("detection_active_streams", "Number of active camera streams")


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
        watch_for_reload=settings.ENABLE_MODEL_HOT_RELOAD,
        watch_interval=settings.MODEL_WATCH_INTERVAL,
        shadow_model_path=(
            settings.SHADOW_MODEL_PATH if settings.ENABLE_SHADOW_MODE else None
        ),
    )
    model.load()
    pipeline = BatchInferencePipeline(model=model, interval=settings.BATCH_INTERVAL)
    if settings.STREAM_CACHE_DIR:
        Path(settings.STREAM_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    _start_buffer_flush_thread()
    _start_dlq_consumer()
    _log_dependency_status()


def _log_dependency_status() -> None:
    deps = get_dependency_report()
    degraded = [name for name, info in deps.items() if info["status"] != "healthy"]
    if degraded:
        logger.warning(
            "Service starting in degraded mode — dependencies down: %s",
            ", ".join(degraded),
        )
    else:
        logger.info("All dependencies healthy")


def _dlq_consumer_loop() -> None:
    try:
        from shared.kafka.consumer import create_consumer

        consumer = create_consumer(
            KAFKA_TOPICS["violations_dlq"],
            group_id="detection-dlq",
        )
        logger.info("DLQ consumer started")
        for msg in consumer:
            logger.warning(
                "DLQ message: key=%s reason=%s topic=%s",
                msg.key,
                msg.value.get("dlq_reason", "unknown"),
                msg.topic,
            )
    except Exception:
        logger.exception("DLQ consumer failed to start")


def _start_dlq_consumer() -> None:
    thread = Thread(target=_dlq_consumer_loop, name="dlq-consumer", daemon=True)
    thread.start()


def _buffer_flush_loop() -> None:
    while True:
        try:
            _flush_violation_buffer()
        except Exception:
            logger.exception("Buffer flush error")
        time.sleep(30)


def _start_buffer_flush_thread() -> None:
    thread = Thread(target=_buffer_flush_loop, name="buffer-flush", daemon=True)
    thread.start()


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


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_DIMENSION = 4096


def _validate_upload(file: UploadFile) -> None:
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}",
        )
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large: {size / 1024 / 1024:.1f}MB "
            f"(max {MAX_IMAGE_SIZE_MB}MB)",
        )


def _validate_frame(frame: np.ndarray) -> None:
    h, w = frame.shape[:2]
    if h > MAX_IMAGE_DIMENSION or w > MAX_IMAGE_DIMENSION:
        raise HTTPException(
            status_code=400,
            detail=f"Image dimensions {w}x{h} exceed maximum "
            f"{MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}",
        )


def _decode_image(file: UploadFile) -> np.ndarray:
    contents = file.file.read()
    arr = np.frombuffer(contents, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    return frame


def _flush_violation_buffer() -> None:
    global _last_flush_attempt
    if not _violation_buffer:
        return
    now = datetime.now(timezone.utc)
    if now - _last_flush_attempt < timedelta(seconds=10):
        return
    _last_flush_attempt = now
    db = get_session()
    try:
        while _violation_buffer:
            entry = _violation_buffer[0]
            violation = Violation(
                id=entry["id"],
                camera_id=entry["camera_id"],
                timestamp=entry["timestamp"],
                coordinates=entry["coordinates"],
                confidence_score=entry["confidence"],
                vehicle_type=entry["vehicle_type"],
                violation_type=entry["violation_type"],
            )
            db.add(violation)
            db.commit()
            with _buffer_lock:
                _violation_buffer.popleft()
            logger.info("Flushed buffered violation %s", entry["id"])
    except Exception:
        db.rollback()
        logger.warning(
            "DB still unavailable — %d violations remain buffered",
            len(_violation_buffer),
        )
    finally:
        db.close()


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
        db = get_session()
        close_session = True

    try:
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
        db.rollback()
        logger.exception("DB unavailable — buffering violation")
        with _buffer_lock:
            _violation_buffer.append(
                {
                    "id": violation_id,
                    "camera_id": uuid.UUID(camera_id) if camera_id else uuid.uuid4(),
                    "timestamp": now,
                    "coordinates": f"SRID=4326;POINT({longitude} {latitude})",
                    "confidence": confidence,
                    "vehicle_type": vehicle_type.value,
                    "violation_type": violation_type,
                    "zone_id": zone_id,
                }
            )
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
        logger.warning("Kafka unreachable — violation %s routed to DLQ", violation_id)
        dlq_ok = producer.send(
            KAFKA_TOPICS["violations_dlq"],
            key=str(violation_id),
            value={**event, "dlq_reason": "kafka_unreachable"},
        )
        if not dlq_ok:
            logger.error(
                "DLQ also unreachable — violation %s persisted to DB only",
                violation_id,
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

    _validate_upload(file)
    frame = _decode_image(file)
    _validate_frame(frame)
    loop = asyncio.get_event_loop()
    inference_start = time.time()
    detections = await loop.run_in_executor(None, model.predict_single, frame)
    DETECTION_LATENCY.observe(time.time() - inference_start)

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
        MODEL_HEALTH.set(1.0 if model.is_loaded() else 0.0)
        ACTIVE_STREAMS.set(stream_manager.camera_count)
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
            DETECTION_FAILURES.labels(reason="db_unavailable").inc()
            raise HTTPException(status_code=503, detail="Database unavailable")
        DETECTION_TOTAL.inc()
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
        _flush_violation_buffer()
        DETECTION_BUFFER_SIZE.set(len(_violation_buffer))

    MODEL_HEALTH.set(1.0 if model.is_loaded() else 0.0)
    ACTIVE_STREAMS.set(stream_manager.camera_count)
    return {"detections": results, "count": len(results)}


def _pipeline_callback(camera_id: str, detections: list[DetectionResult]) -> None:
    config = stream_manager.get_config(camera_id)
    if config and config.roi_polygon:
        detections = [
            d
            for d in detections
            if d.bbox
            and point_in_polygon(
                d.bbox.center[0],
                d.bbox.center[1],
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
        roi_polygon=([tuple(p) for p in req.roi_polygon] if req.roi_polygon else None),
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


@app.get(f"{settings.API_V1_PREFIX}/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain; charset=utf-8",
    )


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    deps = get_dependency_report()
    all_healthy = all(d["status"] == "healthy" for d in deps.values())
    return {
        "status": "ok" if all_healthy else "degraded",
        "service": "detection-service",
        "model_loaded": model.is_loaded() if model else False,
        "active_streams": stream_manager.camera_count,
        "dependencies": deps,
    }
