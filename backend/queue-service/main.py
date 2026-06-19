from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from shared.auth.jwt import require_role
from shared.config.settings import settings
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.congestion_scores import CongestionScore
from shared.models.database import Base, get_db, get_engine
from shared.models.zones import Zone
from shared.redis.client import redis_client

app = FastAPI(title="queue-service", version="1.0.0")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(StructuredLoggingMiddleware)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=get_engine())


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


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"status": "ok", "service": "queue-service"}
