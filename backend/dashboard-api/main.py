from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from shared.auth.jwt import require_role
from shared.config.settings import settings
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.congestion_scores import CongestionScore
from shared.models.database import Base, get_db, get_engine
from shared.models.violations import Violation
from shared.models.zones import Zone
from shared.redis.client import redis_client
from sqlalchemy import Date, cast, func
from sqlalchemy.orm import Session

app = FastAPI(title="dashboard-api", version="1.0.0")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(StructuredLoggingMiddleware)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=get_engine())


@app.on_event("startup")
async def init_redis():
    await redis_client.init()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.get(f"{settings.API_V1_PREFIX}/heatmap")
async def get_heatmap(
    hours: int = Query(24, ge=1, le=168),
    resolution: float = Query(0.001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cache_key = f"heatmap:{hours}:{resolution}"
    cached = await redis_client.get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    grid_size = resolution

    violations = (
        db.query(
            func.floor(func.ST_X(Violation.coordinates) / grid_size).label("grid_x"),
            func.floor(func.ST_Y(Violation.coordinates) / grid_size).label("grid_y"),
            func.count(Violation.id).label("count"),
        )
        .filter(Violation.timestamp >= cutoff)
        .group_by("grid_x", "grid_y")
        .all()
    )

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    (float(v.grid_x) + 0.5) * grid_size,
                    (float(v.grid_y) + 0.5) * grid_size,
                ],
            },
            "properties": {"count": v.count},
        }
        for v in violations
    ]

    geojson = {"type": "FeatureCollection", "features": features}

    await redis_client.set(cache_key, geojson, ttl=settings.HEATMAP_CACHE_TTL)
    return JSONResponse(content=geojson)


@app.get(f"{settings.API_V1_PREFIX}/analytics/trends")
async def get_analytics_trends(
    days: int = Query(30, ge=1, le=365),
    zone_id: str = Query(None),
    vehicle_type: str = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.query(
        cast(Violation.timestamp, Date).label("date"),
        func.count(Violation.id).label("count"),
    ).filter(Violation.timestamp >= cutoff)

    if zone_id:
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        if zone:
            query = query.filter(func.ST_Within(Violation.coordinates, zone.boundary))

    if vehicle_type:
        query = query.filter(Violation.vehicle_type == vehicle_type)

    query = query.group_by(cast(Violation.timestamp, Date)).order_by("date")
    results = query.all()

    return {
        "trends": [{"date": str(r.date), "count": r.count} for r in results],
        "days": days,
        "zone_id": zone_id,
        "vehicle_type": vehicle_type,
    }


@app.get(f"{settings.API_V1_PREFIX}/alerts")
async def get_alerts(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator")),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)

    high_impact_zones = (
        db.query(
            CongestionScore.zone_id,
            func.avg(CongestionScore.impact_score).label("avg_impact"),
            func.sum(CongestionScore.violation_count).label("total_violations"),
        )
        .filter(CongestionScore.timestamp >= cutoff)
        .group_by(CongestionScore.zone_id)
        .having(func.avg(CongestionScore.impact_score) > 60)
        .all()
    )

    zones = db.query(Zone).all()
    zone_map = {str(z.id): z for z in zones}

    alerts = []
    for z in high_impact_zones:
        zone = zone_map.get(str(z.zone_id))
        avg_impact = float(z.avg_impact)
        alerts.append(
            {
                "zone_id": str(z.zone_id),
                "zone_name": zone.name if zone else "Unknown",
                "severity": "CRITICAL" if avg_impact > 80 else "HIGH",
                "average_impact": round(avg_impact, 2),
                "total_violations": int(z.total_violations),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return {"alerts": alerts, "count": len(alerts)}


@app.websocket(f"{settings.API_V1_PREFIX}/alerts/ws")
async def alerts_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get(f"{settings.API_V1_PREFIX}/admin/config")
async def get_config(current_user=Depends(require_role("admin"))):
    return {
        "detection_confidence_threshold": settings.DETECTION_CONFIDENCE_THRESHOLD,
        "frame_sample_interval_seconds": settings.FRAME_SAMPLE_INTERVAL_SECONDS,
        "heatmap_cache_ttl": settings.HEATMAP_CACHE_TTL,
        "priority_queue_cache_ttl": settings.PRIORITY_QUEUE_CACHE_TTL,
        "max_queue_size": settings.MAX_QUEUE_SIZE,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
    }


@app.put(f"{settings.API_V1_PREFIX}/admin/config")
async def update_config(
    config: dict,
    current_user=Depends(require_role("admin")),
):
    for key, value in config.items():
        if hasattr(settings, key.upper()):
            setattr(settings, key.upper(), value)
    return {"status": "updated", "config": config}


@app.websocket(f"{settings.API_V1_PREFIX}/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return {"status": "ok", "service": "dashboard-api"}
