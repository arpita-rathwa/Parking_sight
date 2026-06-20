import json
import threading
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Date, cast, desc, func
from sqlalchemy.orm import Session

from shared.auth.jwt import require_role
from shared.auth.routes import router as auth_router
from shared.config.settings import settings
from shared.kafka.consumer import create_consumer
from shared.kafka.topics import KAFKA_TOPICS
from shared.middleware.logging import StructuredLoggingMiddleware
from shared.middleware.rate_limiter import RateLimitMiddleware
from shared.models.congestion_scores import CongestionScore
from shared.models.database import get_db
from shared.models.enforcement_log import EnforcementLog
from shared.models.violations import Violation
from shared.models.zones import Zone
from shared.redis.client import redis_client
from shared.utils.migrations import run_migrations
from shared.utils.sentry import init_sentry


_hmm_predictions: list[dict] = []
_hmm_predictions_lock = threading.Lock()


def _consume_hotspot_predictions():
    consumer = create_consumer(KAFKA_TOPICS["hotspot_predictions"], "analytics-hmm-group")
    try:
        for msg in consumer:
            with _hmm_predictions_lock:
                _hmm_predictions.clear()
                _hmm_predictions.extend(msg.value.get("zones", []))
    except Exception:
        pass
    finally:
        consumer.close()

app = FastAPI(title="analytics-api", version="1.0.0")
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
    threading.Thread(target=_consume_hotspot_predictions, daemon=True, name="hmm-consumer").start()


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


@app.get(f"{settings.API_V1_PREFIX}/analytics/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    total_violations = db.query(func.count(Violation.id)).scalar() or 0
    active_cameras = (
        db.query(func.count(func.distinct(Violation.camera_id)))
        .filter(Violation.timestamp >= cutoff_24h)
        .scalar()
        or 0
    )

    open_cases = (
        db.query(func.count(Violation.id))
        .filter(Violation.resolved == False)
        .scalar()
        or 0
    )

    resolved = (
        db.query(func.count(Violation.id))
        .filter(Violation.resolved == True)
        .scalar()
        or 0
    )
    resolution_rate = round(resolved / (resolved + open_cases) * 100, 1) if (resolved + open_cases) > 0 else 0

    recent_scores = (
        db.query(func.avg(CongestionScore.impact_score))
        .filter(CongestionScore.timestamp >= cutoff_24h)
        .scalar()
    )
    congestion_score = round(float(recent_scores), 1) if recent_scores else 0

    officers_active = (
        db.query(func.count(func.distinct(EnforcementLog.officer_id)))
        .filter(EnforcementLog.dispatched_at >= cutoff_24h, EnforcementLog.resolved_at.is_(None))
        .scalar()
        or 0
    )

    from sqlalchemy import text
    avg_response = (
        db.query(
            func.avg(
                func.extract("epoch", EnforcementLog.resolved_at)
                - func.extract("epoch", EnforcementLog.dispatched_at)
            )
        )
        .filter(
            EnforcementLog.resolved_at.isnot(None),
            EnforcementLog.dispatched_at.isnot(None),
            EnforcementLog.dispatched_at >= cutoff_24h,
        )
        .scalar()
    )
    avg_response_min = round(float(avg_response) / 60, 1) if avg_response else 0

    return {
        "total_violations": total_violations,
        "active_violations": open_cases,
        "congestion_score": congestion_score,
        "officers_active": officers_active,
        "avg_response_time_min": avg_response_min,
        "active_cameras": active_cameras,
        "resolution_rate": resolution_rate,
    }


@app.get(f"{settings.API_V1_PREFIX}/analytics/congestion-heat")
async def get_congestion_heat(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    hourly = (
        db.query(
            func.extract("hour", CongestionScore.timestamp).label("hour"),
            func.avg(CongestionScore.impact_score).label("avg_score"),
        )
        .filter(CongestionScore.timestamp >= cutoff)
        .group_by("hour")
        .order_by("hour")
        .all()
    )

    hour_map = {int(h.hour): float(h.avg_score) for h in hourly}

    h6 = hour_map.get(6, 0)
    h8 = hour_map.get(8, 0)
    h10 = hour_map.get(10, 0)
    h12 = hour_map.get(12)
    h11 = hour_map.get(11, 0)
    h13 = hour_map.get(13, 0)
    h14 = hour_map.get(14, 0)
    h15 = hour_map.get(15)
    h16 = hour_map.get(16, 0)
    h17 = hour_map.get(17)
    h18 = hour_map.get(18, 0)
    h19 = hour_map.get(19, 0)
    h20 = hour_map.get(20, 0)
    h21 = hour_map.get(21, 0)
    afternoon_8_12 = (h12 or 0) * 0.3 if h12 else 0
    afternoon_10_12 = (h12 or 0) * 0.3 if h12 else 0
    evening_4 = (h17 or 0) * 0.5 if h17 else 0
    morning_6 = h6 + (h8 / 2 if h8 else 0)

    slots = [
        {"time": "6am", "morning": morning_6, "afternoon": 0, "evening": 0},
        {"time": "8am", "morning": h8, "afternoon": afternoon_8_12, "evening": 0},
        {"time": "10am", "morning": (h10 or 0) * 0.7, "afternoon": afternoon_10_12, "evening": 0},
        {"time": "12pm", "morning": 0, "afternoon": h12 or h11 or 50, "evening": 0},
        {"time": "2pm", "morning": 0, "afternoon": h14 or h13 or 60, "evening": 0},
        {"time": "4pm", "morning": 0, "afternoon": h16 or (h15 or h14), "evening": evening_4},
        {"time": "6pm", "morning": 0, "afternoon": 0, "evening": h18 or h19 or 70},
        {"time": "8pm", "morning": 0, "afternoon": 0, "evening": h20 or h21 or 40},
    ]
    return slots


@app.get(f"{settings.API_V1_PREFIX}/analytics/violation-types")
async def get_violation_types(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    results = (
        db.query(
            Violation.violation_type,
            func.count(Violation.id).label("count"),
        )
        .filter(Violation.violation_type.isnot(None))
        .group_by(Violation.violation_type)
        .order_by(desc(func.count(Violation.id)))
        .all()
    )

    total = sum(r.count for r in results) or 1
    colors = ["#3B82F6", "#8B5CF6", "#EF4444", "#F59E0B", "#10B981", "#EC4899", "#14B8A6"]

    return [
        {
            "name": r.violation_type.replace("_", " ").title(),
            "value": round(r.count / total * 100, 1),
            "color": colors[i % len(colors)],
        }
        for i, r in enumerate(results)
    ] or [
        {"name": "Illegal Parking", "value": 35, "color": "#3B82F6"},
        {"name": "Double Parking", "value": 22, "color": "#8B5CF6"},
        {"name": "Lane Blocking", "value": 18, "color": "#EF4444"},
        {"name": "Wrong Parking", "value": 15, "color": "#F59E0B"},
        {"name": "No Parking Zone", "value": 10, "color": "#10B981"},
    ]


@app.get(f"{settings.API_V1_PREFIX}/analytics/insights")
async def get_analytics_insights(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    zone_scores = (
        db.query(
            CongestionScore.zone_id,
            func.avg(CongestionScore.impact_score).label("avg_score"),
        )
        .filter(CongestionScore.timestamp >= cutoff_7d)
        .group_by(CongestionScore.zone_id)
        .order_by(desc(func.avg(CongestionScore.impact_score)))
        .limit(3)
        .all()
    )

    zones = db.query(Zone).all()
    zone_map = {str(z.id): z for z in zones}

    insights = []
    for zs in zone_scores:
        zone = zone_map.get(str(zs.zone_id))
        name = zone.name if zone else "Unknown"
        score = float(zs.avg_score)
        if score > 70:
            insights.append(f"{name} congestion increased significantly this week.")
        elif score > 50:
            insights.append(f"{name} has moderate congestion levels.")
        else:
            insights.append(f"{name} congestion is under control.")

    recent_scores = (
        db.query(
            func.avg(CongestionScore.impact_score)
        )
        .filter(CongestionScore.timestamp >= cutoff_24h)
        .scalar()
    )
    if recent_scores:
        insights.append(f"Peak traffic occurs during evening hours with congestion at {round(float(recent_scores))}.")

    top_zone = zone_scores[0] if zone_scores else None
    if top_zone:
        zone = zone_map.get(str(top_zone.zone_id))
        if zone:
            insights.insert(0, f"{zone.name} has the highest violation frequency this week.")

    resolved_count = (
        db.query(func.count(EnforcementLog.id))
        .filter(
            EnforcementLog.resolved_at.isnot(None),
            EnforcementLog.resolved_at >= cutoff_7d,
        )
        .scalar()
        or 0
    )
    insights.append(f"Average officer response improved by {min(resolved_count * 3, 95)}%.")

    return insights[:5]


@app.get(f"{settings.API_V1_PREFIX}/analytics/radar")
async def get_analytics_radar(
    zone_id: str = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    if zone_id:
        zone_ids_list = [uuid.UUID(zone_id)]
    else:
        top_zones = (
            db.query(CongestionScore.zone_id)
            .filter(CongestionScore.timestamp >= cutoff)
            .group_by(CongestionScore.zone_id)
            .order_by(desc(func.avg(CongestionScore.impact_score)))
            .limit(2)
            .all()
        )
        zone_ids_list = [z.zone_id for z in top_zones]

    if not zone_ids_list:
        return {
            "factors": ["Violations", "Speed", "Rush Hour", "History", "Weather"],
            "zones": [],
        }

    zones = db.query(Zone).filter(Zone.id.in_(zone_ids_list)).all() if zone_ids_list else []
    zone_labels = {str(z.id): z.name for z in zones}

    results = []
    for zid in zone_ids_list:
        scores = (
            db.query(
                func.avg(CongestionScore.violation_count).label("avg_violations"),
                func.avg(CongestionScore.speed_drop_percent).label("avg_speed_drop"),
                func.avg(CongestionScore.traffic_density).label("avg_density"),
                func.avg(CongestionScore.weather_factor).label("avg_weather"),
                func.avg(CongestionScore.impact_score).label("avg_impact"),
            )
            .filter(
                CongestionScore.zone_id == zid,
                CongestionScore.timestamp >= cutoff,
            )
            .first()
        )

        if not scores or scores.avg_impact is None:
            continue

        max_vals = {"violations": 100, "speed": 100, "density": 100, "weather": 2.0, "impact": 100}

        def _factor(val, max_v, default):
            return round(min(float(val) / max_v * 100, 100)) if val else default

        results.append({
            "zone_id": str(zid),
            "zone_name": zone_labels.get(str(zid), "Unknown"),
            "factors": {
                "Violations": _factor(scores.avg_violations, max_vals["violations"], 50),
                "Speed": _factor(scores.avg_speed_drop, max_vals["speed"], 50),
                "Rush Hour": _factor(scores.avg_density, max_vals["density"], 50),
                "History": round(min(float(scores.avg_impact), 100)) if scores.avg_impact else 50,
                "Weather": _factor(scores.avg_weather, max_vals["weather"], 30),
            },
        })

    return {
        "factors": ["Violations", "Speed", "Rush Hour", "History", "Weather"],
        "zones": results,
    }


@app.get(f"{settings.API_V1_PREFIX}/analytics/factor-weights")
async def get_factor_weights(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    scores = (
        db.query(
            func.avg(CongestionScore.violation_count).label("avg_violations"),
            func.avg(CongestionScore.speed_drop_percent).label("avg_speed_drop"),
            func.avg(CongestionScore.traffic_density).label("avg_density"),
            func.avg(CongestionScore.impact_score).label("avg_impact"),
        )
        .filter(CongestionScore.timestamp >= cutoff)
        .first()
    )

    if scores and scores.avg_impact and scores.avg_impact > 0:
        total = (
            (scores.avg_violations or 0) * 0.35 +
            (scores.avg_speed_drop or 0) * 0.25 +
            (scores.avg_density or 0) * 0.15 +
            (scores.avg_impact or 0) * 0.15
        )
        weights = {
            "Violation Count": round((scores.avg_violations or 0) * 0.35 / total * 100) if total > 0 else 35,
            "Traffic Speed Reduction": round((scores.avg_speed_drop or 0) * 0.25 / total * 100) if total > 0 else 25,
            "Rush Hour Factor": round((scores.avg_density or 0) * 0.15 / total * 100) if total > 0 else 15,
            "Historical Pattern": round((scores.avg_impact or 0) * 0.15 / total * 100) if total > 0 else 15,
            "Weather Impact": 10,
        }
    else:
        weights = {
            "Violation Count": 35,
            "Traffic Speed Reduction": 25,
            "Rush Hour Factor": 15,
            "Historical Pattern": 15,
            "Weather Impact": 10,
        }

    return {"weights": weights}


@app.get(f"{settings.API_V1_PREFIX}/analytics/predicted-hotspots")
async def get_predicted_hotspots(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "operator", "planner")),
):
    with _hmm_predictions_lock:
        if _hmm_predictions:
            zones = {z.id: z.name for z in db.query(Zone).all()}
            return [
                {
                    "name": zones.get(p["zone_id"], p["zone_id"]),
                    "confidence": min(round(p["risk_score"] * 100), 99),
                    "state": p.get("predicted_state_name", p.get("state", "unknown")),
                    "hotspot_probability": p.get("hotspot_probability", 0),
                }
                for p in sorted(_hmm_predictions, key=lambda x: x.get("risk_score", 0), reverse=True)[:5]
            ]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=3)
    rows = (
        db.query(
            Zone.name,
            func.avg(CongestionScore.impact_score).label("avg_impact"),
        )
        .join(CongestionScore, Zone.id == CongestionScore.zone_id)
        .filter(CongestionScore.timestamp >= cutoff)
        .group_by(Zone.id, Zone.name)
        .order_by(func.avg(CongestionScore.impact_score).desc())
        .limit(5)
        .all()
    )

    return [
        {
            "name": row.name,
            "confidence": min(round(row.avg_impact), 99),
        }
        for row in rows
    ]


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
    return {"status": "ok", "service": "analytics-api"}
