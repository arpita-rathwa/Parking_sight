"""HMM inference — per-zone hotspot forecast for the next 30-min bin.

Math (deliberately simple and explainable):
  1. take the zone's recent observation window
  2. forward algorithm -> posterior belief over the CURRENT regime  (predict_proba)
  3. one-step transition:  next_belief = current_belief @ A
  4. derive demo-friendly numbers from next_belief (in severity order):
        risk_score          = next_belief · severity_weights        (0..1)
        hotspot_probability = P(next regime in {congested, critical})
        escalation_prob     = P(next regime is worse than current)
"""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path

import numpy as np

from common.config import get_settings
from common.db import session_scope
from common.kafka_producer import emit_hotspot_predictions
from common.logging import get_logger
from common.models import HmmPrediction
from common.storage import Storage
from hmm_prediction import features
from hmm_prediction.states import hot_state_indices, severity_weights
from hmm_prediction.train_hmm import META_KEY, MODEL_KEY

log = get_logger("hmm.infer")
_CACHE: dict | None = None


def _load():
    global _CACHE
    if _CACHE is None:
        import joblib

        s = get_settings()
        storage = Storage()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "model.joblib"
            storage.get_file(s.s3_bucket_models, MODEL_KEY, p)
            bundle = joblib.load(p)
        meta = storage.get_json(s.s3_bucket_models, META_KEY)
        _CACHE = {"model": bundle["model"], "scaler": bundle["scaler"], "meta": meta}
    return _CACHE["model"], _CACHE["scaler"], _CACHE["meta"]


def reset_cache() -> None:
    global _CACHE
    _CACHE = None


def _explain(zone_id, X, current_idx, predicted_idx, names, hotspot, risk, escalation) -> str:
    recent_viol = float(np.mean(X[-4:, features.FEATURE_NAMES.index("violation_count")])) if len(X) else 0.0
    trend = "rising" if len(X) >= 2 and X[-1, 0] > X[-min(4, len(X)), 0] else "steady"
    verb = "escalate" if predicted_idx > current_idx else ("ease" if predicted_idx < current_idx else "hold")
    return (
        f"Zone {zone_id} is in a '{names[current_idx]}' regime ({trend} congestion, "
        f"~{recent_viol:.0f} recent violations). Learned transition patterns put a "
        f"{hotspot * 100:.0f}% chance of a congested/critical regime in the next 30 min "
        f"(risk {risk:.2f}); the regime is most likely to {verb} to '{names[predicted_idx]}'."
    )


def forecast_zone(zone_id: str, persist: bool = True) -> dict:
    s = get_settings()
    model, scaler, meta = _load()
    n = meta["n_states"]
    names = meta["state_names"]
    perm = meta["perm"]
    weights = severity_weights(n)

    X, ts = features.zone_matrix(zone_id, limit=s.hmm_window)
    for_ts = (ts[-1] + dt.timedelta(minutes=s.hmm_bin_minutes)) if ts else dt.datetime.now(dt.timezone.utc)

    if len(X) < s.hmm_min_history:
        # cold start: simple recent-severity heuristic, flagged low-confidence
        recent_impact = float(np.mean(X[:, 0])) if len(X) else 0.0
        result = {
            "zone_id": zone_id,
            "for_timestamp": for_ts,
            "current_state": 0,
            "current_state_name": names[0],
            "predicted_state": 0,
            "predicted_state_name": names[0],
            "hotspot_probability": 0.0,
            "risk_score": min(1.0, recent_impact),
            "escalation_probability": 0.0,
            "insufficient_history": True,
            "explanation": f"Zone {zone_id}: insufficient history for HMM forecast; "
            f"showing recent-average risk only.",
        }
    else:
        Xs = scaler.transform(X)
        gamma = model.predict_proba(Xs)  # posteriors, model-state order
        belief = gamma[-1]  # belief over CURRENT regime
        nxt = belief @ model.transmat_  # one-step-ahead, model-state order
        belief_sev = belief[perm]  # reorder to severity space
        nxt_sev = nxt[perm]

        current_idx = int(np.argmax(belief_sev))
        predicted_idx = int(np.argmax(nxt_sev))
        risk = float(nxt_sev @ weights)
        hotspot = float(sum(nxt_sev[k] for k in hot_state_indices(n)))
        escalation = float(sum(nxt_sev[k] for k in range(current_idx + 1, n)))

        result = {
            "zone_id": zone_id,
            "for_timestamp": for_ts,
            "current_state": current_idx,
            "current_state_name": names[current_idx],
            "predicted_state": predicted_idx,
            "predicted_state_name": names[predicted_idx],
            "hotspot_probability": round(hotspot, 4),
            "risk_score": round(risk, 4),
            "escalation_probability": round(escalation, 4),
            "insufficient_history": False,
            "explanation": _explain(zone_id, X, current_idx, predicted_idx, names, hotspot, risk, escalation),
        }

    if persist:
        with session_scope() as db:
            db.add(
                HmmPrediction(
                    zone_id=zone_id,
                    for_timestamp=result["for_timestamp"],
                    current_state=result["current_state"],
                    current_state_name=result["current_state_name"],
                    predicted_state=result["predicted_state"],
                    predicted_state_name=result["predicted_state_name"],
                    hotspot_probability=result["hotspot_probability"],
                    risk_score=result["risk_score"],
                    escalation_probability=result["escalation_probability"],
                    insufficient_history=result["insufficient_history"],
                )
            )
    return result


def forecast_all(persist: bool = True) -> list[dict]:
    preds = [forecast_zone(z, persist=persist) for z in features.list_zones()]
    preds.sort(key=lambda p: p["risk_score"], reverse=True)
    if preds:
        emit_hotspot_predictions(
            [
                {k: p[k] for k in ("zone_id", "risk_score", "hotspot_probability", "predicted_state_name")}
                for p in preds
            ]
        )
    log.info("forecast_all_done", n_zones=len(preds), top_zone=preds[0]["zone_id"] if preds else None)
    return preds


def heatmap_payload() -> list[dict]:
    """Heatmap-friendly: one row per zone with risk for the map overlay.
    Frontend joins zone_id -> zone boundary (PostGIS) for rendering."""
    return [
        {
            "zone_id": p["zone_id"],
            "risk_score": p["risk_score"],
            "hotspot_probability": p["hotspot_probability"],
            "state": p["predicted_state_name"],
        }
        for p in forecast_all(persist=False)
    ]
