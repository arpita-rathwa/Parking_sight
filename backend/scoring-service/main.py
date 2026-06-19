from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from shared.auth.jwt import require_role
from shared.config.settings import settings
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.congestion_scores import CongestionScore
from shared.models.database import Base, get_db, get_engine
from shared.models.violations import Violation
from shared.models.zones import Zone
from shared.redis.client import redis_client
from sqlalchemy import func
from sqlalchemy.orm import Session

app = FastAPI(title="scoring-service", version="1.0.0")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(StructuredLoggingMiddleware)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=get_engine())


@app.on_event("startup")
async def init_redis():
    await redis_client.init()


@app.get(f"{settings.API_V1_PREFIX}/zones/{{zone_id}}/impact")
async def get_zone_impact(
    zone_id: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cache_key = f"zone_impact:{zone_id}:{hours}"
    cached = await redis_client.get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    scores = (
        db.query(CongestionScore)
        .filter(
            CongestionScore.zone_id == zone_id,
            CongestionScore.timestamp >= cutoff,
        )
        .order_by(CongestionScore.timestamp)
        .all()
    )

    violation_count = (
        db.query(func.count(Violation.id))
        .filter(
            Violation.timestamp >= cutoff,
            func.ST_Within(
                Violation.coordinates,
                zone.boundary,
            ),
        )
        .scalar()
    )

    avg_impact = sum(s.impact_score for s in scores) / len(scores) if scores else 0
    result = {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "hours": hours,
        "violation_count": violation_count,
        "impact_scores": [
            {
                "timestamp": s.timestamp.isoformat(),
                "impact_score": s.impact_score,
                "speed_drop_percent": s.speed_drop_percent,
                "violation_count": s.violation_count,
            }
            for s in scores
        ],
        "average_impact": avg_impact,
    }

    await redis_client.set(cache_key, result, ttl=settings.HEATMAP_CACHE_TTL)
    return result


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"status": "ok", "service": "scoring-service"}
