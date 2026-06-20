import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import lightgbm as lgb
import pandas as pd

app = FastAPI(title="Parking Hotspot Scoring Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_model_path = os.path.join(os.path.dirname(__file__), "..", "model", "model.txt")
try:
    model = lgb.Booster(model_file=_model_path)
except Exception as e:
    raise RuntimeError(f"Failed to load model from {_model_path}: {e}")

FEATURE_COLS = [
    "raw_count", "centroid_lat", "centroid_lon", "police_station",
    "junction_name", "n_unique_devices", "n_unique_vehicles",
    "pct_approved", "pct_weekend", "mode_hour", "hour_std"
]

class ClusterFeatures(BaseModel):
    cluster_id: int
    raw_count: float
    centroid_lat: float
    centroid_lon: float
    police_station: str
    junction_name: str
    n_unique_devices: float
    n_unique_vehicles: float
    pct_approved: float
    pct_weekend: float
    mode_hour: float
    hour_std: float

@app.post("/score")
def score_cluster(features: ClusterFeatures):
    try:
        row = pd.DataFrame([features.model_dump()])
        row["police_station"] = row["police_station"].astype("category")
        row["junction_name"] = row["junction_name"].astype("category")
        score = float(model.predict(row[FEATURE_COLS])[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    tier = "HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "LOW")
    return {
        "cluster_id": features.cluster_id,
        "predicted_impact_score": round(score, 4),
        "priority_tier": tier
    }

@app.get("/health")
def health():
    return {"status": "ok"}