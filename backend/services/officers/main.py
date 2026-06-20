from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.auth.jwt import require_role
from shared.auth.routes import router as auth_router
from shared.config.settings import settings
from shared.kafka.producer import producer
from shared.kafka.topics import KAFKA_TOPICS
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.database import Base, get_db, get_engine
from shared.models.enforcement_log import EnforcementLog
from shared.models.users import User
from shared.models.zones import Zone
from shared.utils.migrations import run_migrations
from shared.utils.sentry import init_sentry

app = FastAPI(title="officers-api", version="1.0.0")
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


@app.on_event("startup")
def on_startup():
    run_migrations()
    init_sentry(settings.SERVICE_NAME)


class StatusUpdate(BaseModel):
    assignment_id: str
    status: str
    notes: str = ""


@app.get(f"{settings.API_V1_PREFIX}/officer/assignments")
async def get_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    assignments = (
        db.query(EnforcementLog, Zone)
        .join(Zone, EnforcementLog.zone_id == Zone.id)
        .filter(
            EnforcementLog.officer_id == current_user.id,
            EnforcementLog.resolved_at.is_(None),
        )
        .order_by(EnforcementLog.dispatched_at.desc())
        .all()
    )

    return [
        {
            "assignment_id": str(log.id),
            "zone_id": str(log.zone_id),
            "zone_name": zone.name,
            "police_station": zone.police_station,
            "dispatched_at": log.dispatched_at.isoformat(),
            "outcome": log.outcome,
        }
        for log, zone in assignments
    ]


@app.post(f"{settings.API_V1_PREFIX}/officer/status")
async def update_status(
    update: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    log = (
        db.query(EnforcementLog)
        .filter(EnforcementLog.id == update.assignment_id)
        .first()
    )
    if not log:
        raise HTTPException(status_code=404, detail="Assignment not found")

    now = datetime.now(timezone.utc)

    if update.status == "en_route":
        log.arrived_at = None
    elif update.status == "on_scene":
        log.arrived_at = now
    elif update.status == "resolved":
        log.resolved_at = now
        log.outcome = "resolved"
    elif update.status == "unresolvable":
        log.resolved_at = now
        log.outcome = "unresolvable"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")

    log.notes = update.notes
    db.commit()

    event = {
        "assignment_id": str(log.id),
        "officer_id": str(current_user.id),
        "zone_id": str(log.zone_id),
        "status": update.status,
        "timestamp": now.isoformat(),
    }
    producer.send(KAFKA_TOPICS["enforcement_updates"], key=str(log.id), value=event)

    if update.status == "unresolvable":
        feedback_event = {
            "event": "officer.feedback",
            "schema_version": 1,
            "feedback_id": str(log.id),
            "violation_id": str(log.zone_id),
            "officer_id": str(current_user.id),
            "zone_id": str(log.zone_id),
            "status": "unresolvable",
            "reason": update.notes,
            "timestamp": now.isoformat(),
        }
        producer.send(KAFKA_TOPICS["officer_feedback"], key=str(log.id), value=feedback_event)

    return {
        "status": "updated",
        "assignment_id": str(log.id),
        "new_status": update.status,
    }


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"status": "ok", "service": "officers-api"}
