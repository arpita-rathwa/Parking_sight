import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, UploadFile
from pydantic import BaseModel
from shared.auth.jwt import require_role
from shared.config.settings import settings
from shared.kafka.producer import producer
from shared.kafka.topics import KAFKA_TOPICS
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.database import Base, get_db, get_engine
from shared.models.violations import Violation
from sqlalchemy.orm import Session

app = FastAPI(title="detection-service", version="1.0.0")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(StructuredLoggingMiddleware)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=get_engine())


class DetectionResult(BaseModel):
    id: str
    camera_id: str
    timestamp: str
    latitude: float
    longitude: float
    confidence_score: float
    vehicle_type: str
    violation_type: str


@app.post(f"{settings.API_V1_PREFIX}/detect")
async def detect_violation(
    camera_id: str,
    latitude: float,
    longitude: float,
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator")),
):
    violation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    violation = Violation(
        id=violation_id,
        camera_id=uuid.UUID(camera_id),
        timestamp=now,
        coordinates=f"SRID=4326;POINT({longitude} {latitude})",
        confidence_score=settings.DETECTION_CONFIDENCE_THRESHOLD,
        vehicle_type="unknown",
        violation_type="unknown",
    )
    db.add(violation)
    db.commit()

    event = {
        "violation_id": str(violation_id),
        "camera_id": camera_id,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": now.isoformat(),
        "confidence": settings.DETECTION_CONFIDENCE_THRESHOLD,
    }
    producer.send(KAFKA_TOPICS["violations_raw"], key=str(violation_id), value=event)

    return DetectionResult(
        id=str(violation_id),
        camera_id=camera_id,
        timestamp=now.isoformat(),
        latitude=latitude,
        longitude=longitude,
        confidence_score=settings.DETECTION_CONFIDENCE_THRESHOLD,
        vehicle_type="unknown",
        violation_type="unknown",
    )


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"status": "ok", "service": "detection-service"}
