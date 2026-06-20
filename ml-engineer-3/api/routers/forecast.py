"""HMM pre-staging endpoints — hotspot forecasts for the dashboard overlay."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import require_role
from hmm_prediction import infer

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])


@router.post("/hotspots")
def forecast_hotspots(_role: str = Depends(require_role("operator", "planner", "admin"))):
    """Run the HMM forecast for all zones, ranked by next-window risk."""
    try:
        return {"zones": infer.forecast_all(persist=True)}
    except FileNotFoundError:
        raise HTTPException(409, "no trained HMM yet — run training first (make train-hmm)")


@router.get("/heatmap")
def forecast_heatmap(_role: str = Depends(require_role("operator", "planner", "admin"))):
    """Heatmap-friendly risk per zone for the map overlay."""
    try:
        return {"horizon_minutes": 30, "zones": infer.heatmap_payload()}
    except FileNotFoundError:
        raise HTTPException(409, "no trained HMM yet — run training first (make train-hmm)")


@router.get("/zones/{zone_id}")
def forecast_zone(zone_id: str, _role: str = Depends(require_role("operator", "planner", "admin"))):
    """Forecast + plain-language explanation for one zone."""
    try:
        return infer.forecast_zone(zone_id, persist=True)
    except FileNotFoundError:
        raise HTTPException(409, "no trained HMM yet — run training first (make train-hmm)")
