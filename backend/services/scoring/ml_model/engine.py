import json
import logging
import os
from typing import Any

logger = logging.getLogger("ml-scoring-engine")

FEATURE_COLS = [
    "raw_count",
    "centroid_lat",
    "centroid_lon",
    "n_unique_devices",
    "n_unique_vehicles",
    "pct_approved",
    "pct_weekend",
    "mode_hour",
    "hour_std",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.txt")
CLUSTER_PATH = os.path.join(BASE_DIR, "cluster_summary.json")


class MLScoringEngine:
    def __init__(self):
        self._model: Any = None
        self._cluster_stats: dict[str, float] = {}

    def load(self) -> bool:
        try:
            import lightgbm as lgb
        except ImportError:
            logger.warning("lightgbm not installed — ML scoring unavailable")
            return False

        try:
            self._model = lgb.Booster(model_file=MODEL_PATH)
            logger.info("LightGBM model loaded from %s", MODEL_PATH)
        except Exception:
            logger.exception("Failed to load LightGBM model")
            return False

        try:
            with open(CLUSTER_PATH) as f:
                clusters = json.load(f)
            if clusters:
                self._cluster_stats = {
                    "avg_severity": sum(c.get("avg_severity", 0.5) for c in clusters)
                    / len(clusters),
                    "avg_days": sum(c.get("distinct_days", 1) for c in clusters)
                    / len(clusters),
                }
            logger.info("Loaded cluster summary with %d clusters", len(clusters))
        except Exception:
            logger.warning("Failed to load cluster summary, using defaults")

        return True

    def is_loaded(self) -> bool:
        return self._model is not None

    def predict_impact(self, zone_data: dict) -> float:
        if not self._model:
            return self._heuristic_score(zone_data)

        try:
            import pandas as pd

            row = {
                "raw_count": zone_data.get("violation_count", 0),
                "centroid_lat": zone_data.get("lat", 12.97),
                "centroid_lon": zone_data.get("lon", 77.59),
                "n_unique_devices": zone_data.get("n_unique_devices", 1),
                "n_unique_vehicles": zone_data.get("violation_count", 0),
                "pct_approved": zone_data.get("pct_approved", 0.5),
                "pct_weekend": zone_data.get("pct_weekend", 0.3),
                "mode_hour": float(zone_data.get("mode_hour", 14)),
                "hour_std": zone_data.get("hour_std", 3.0),
            }
            df = pd.DataFrame([row])
            score = float(self._model.predict(df[FEATURE_COLS])[0])
            return max(0, min(100, score))
        except Exception:
            logger.exception("ML prediction failed, falling back to heuristic")
            return self._heuristic_score(zone_data)

    def _heuristic_score(self, zone_data: dict) -> float:
        count = zone_data.get("violation_count", 0)
        max_count = zone_data.get("max_zone_count", 1) or 1
        return round(min(count / max_count * 100, 100), 2)


_engine: MLScoringEngine | None = None


def get_scoring_engine() -> MLScoringEngine:
    global _engine
    if _engine is None:
        _engine = MLScoringEngine()
        _engine.load()
    return _engine


def reload_scoring_engine(model_path: str | None = None) -> bool:
    global _engine
    if model_path:
        logger.info("Reloading scoring engine from promoted model: %s", model_path)
        import shutil
        try:
            shutil.copy(model_path, MODEL_PATH)
        except Exception:
            logger.exception("Failed to copy promoted model, reloading from existing")
    _engine = MLScoringEngine()
    ok = _engine.load()
    return ok
