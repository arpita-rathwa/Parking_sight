import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from shared.auth.jwt import require_role
from shared.auth.routes import router as auth_router
from shared.config.settings import settings
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.congestion_scores import CongestionScore
from shared.models.database import Base, get_db, get_engine
from shared.models.enforcement_log import EnforcementLog
from shared.models.users import User
from shared.models.zones import Zone
from shared.redis.client import redis_client
from shared.utils.migrations import run_migrations
from shared.utils.sentry import init_sentry

app = FastAPI(title="dispatch-service", version="1.0.0")
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


@app.on_event("startup")
async def init_redis():
    await redis_client.init()


@app.get(f"{settings.API_V1_PREFIX}/priority-queue")
async def get_priority_queue(
    top_n: int = Query(10, ge=1, le=100),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator")),
):
    cache_key = f"priority_queue:{top_n}:{hours}"
    cached = await redis_client.get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    latest_scores = (
        db.query(
            CongestionScore.zone_id,
            func.avg(CongestionScore.impact_score).label("avg_impact"),
            func.avg(CongestionScore.speed_drop_percent).label("avg_speed_drop"),
            func.sum(CongestionScore.violation_count).label("total_violations"),
        )
        .filter(CongestionScore.timestamp >= cutoff)
        .group_by(CongestionScore.zone_id)
        .order_by(desc(func.avg(CongestionScore.impact_score)))
        .limit(top_n)
        .all()
    )

    zones = db.query(Zone).all()
    zone_map = {str(z.id): z for z in zones}

    queue = []
    for idx, score in enumerate(latest_scores):
        zone = zone_map.get(str(score.zone_id))
        if not zone:
            continue
        avg_impact = float(score.avg_impact)
        recommendation = (
            "IMMEDIATE"
            if avg_impact > 70
            else "HIGH" if avg_impact > 50 else "MEDIUM" if avg_impact > 30 else "LOW"
        )
        queue.append(
            {
                "rank": idx + 1,
                "zone_id": str(score.zone_id),
                "zone_name": zone.name if zone else "Unknown",
                "police_station": zone.police_station,
                "average_impact": round(avg_impact, 2),
                "speed_drop_percent": round(float(score.avg_speed_drop), 2),
                "total_violations": int(score.total_violations),
                "recommendation": recommendation,
            }
        )

    await redis_client.set(cache_key, queue, ttl=settings.PRIORITY_QUEUE_CACHE_TTL)

    await redis_client.client.zadd(
        "priority_queue",
        {item["zone_id"]: -item["rank"] for item in queue},
    )

    return queue


@app.get(f"{settings.API_V1_PREFIX}/dispatch/overview")
async def get_dispatch_overview(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator")),
):
    all_zones = db.query(Zone).all()
    zone_map = {str(z.id): z for z in all_zones}

    active_logs = (
        db.query(EnforcementLog)
        .filter(EnforcementLog.resolved_at.is_(None))
        .order_by(EnforcementLog.dispatched_at.desc())
        .all()
    )
    log_map: dict[str, EnforcementLog] = {}
    for log in active_logs:
        oid = str(log.officer_id)
        if oid not in log_map:
            log_map[oid] = log

    officers_data = (
        db.query(User)
        .filter(User.role == "officer", User.is_active.is_(True))
        .all()
    )

    officers = []
    for u in officers_data:
        uid = str(u.id)
        log = log_map.get(uid)
        status = "Available"
        zone_name = "—"
        stat_label = "Response"
        stat_val = "—"
        color = "green"
        if log:
            zone_obj = zone_map.get(str(log.zone_id))
            zone_name = zone_obj.name if zone_obj else "Unknown"
            if log.arrived_at is not None:
                status = "On Scene"
                color = "orange"
                stat_label = "Response"
                diff = (datetime.now(timezone.utc) - log.dispatched_at).total_seconds() / 60
                stat_val = f"{diff:.1f} min"
            elif log.dispatched_at is not None:
                status = "En Route"
                color = "blue"
                stat_label = "ETA"
                remaining = max(0, 10 - (datetime.now(timezone.utc) - log.dispatched_at).total_seconds() / 60)
                stat_val = f"{remaining:.0f} min"

        officers.append({
            "id": uid,
            "name": u.full_name,
            "status": status,
            "zone": zone_name,
            "statLabel": stat_label,
            "statVal": stat_val,
            "color": color,
        })

    active_logs_list = list(active_logs)[:20]
    assignments = []
    for log in active_logs_list:
        oid = str(log.officer_id)
        officer_name = "Unknown"
        o_user = db.query(User).filter(User.id == log.officer_id).first()
        if o_user:
            officer_name = o_user.full_name
        zone = zone_map.get(str(log.zone_id))
        zone_name_a = zone.name if zone else "Unknown Zone"
        status = "EN ROUTE"
        color = "blue"
        eta = "—"
        if log.arrived_at is not None:
            status = "ON SCENE"
            color = "orange"
            eta = "On Scene"
        elif log.dispatched_at is not None:
            remaining = max(0, 10 - (datetime.now(timezone.utc) - log.dispatched_at).total_seconds() / 60)
            eta = f"{remaining:.0f} min"
        ps = zone.priority_score if zone and zone.priority_score else 50
        priority = "CRITICAL" if ps > 80 else "HIGH" if ps > 60 else "MEDIUM"

        assignments.append({
            "officer": officer_name,
            "zone": zone_name_a,
            "violation": "—",
            "priority": priority,
            "eta": eta,
            "status": status,
            "color": color,
        })

    recent_logs = (
        db.query(EnforcementLog)
        .order_by(desc(EnforcementLog.dispatched_at))
        .limit(20)
        .all()
    )

    timeline = []
    for log in recent_logs:
        oid = str(log.officer_id)
        officer_name = "Unknown"
        o_user = db.query(User).filter(User.id == log.officer_id).first()
        if o_user:
            officer_name = o_user.full_name
        zone = zone_map.get(str(log.zone_id))
        zone_name_t = zone.name if zone else "Unknown Zone"
        if log.resolved_at is not None:
            action = "resolved case at"
        elif log.arrived_at is not None:
            action = "reached"
        else:
            action = "dispatched to"
        timeline.append({
            "time": log.dispatched_at.strftime("%I:%M %p").lstrip("0"),
            "text": f"Officer {officer_name} {action} {zone_name_t}",
            "icon": "dispatch",
        })

    return {
        "officers": officers,
        "assignments": assignments,
        "timeline": timeline,
    }


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"status": "ok", "service": "dispatch-service"}
