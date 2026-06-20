"""Feature engineering for the HMM.

Each observation (one zone, one 30-min bin) is the vector:
    [impact_score, violation_count, speed_drop_percent, hour_sin, hour_cos]

The first three are the congestion signal; the cyclical hour features let the
model associate regimes with time-of-day (rush hours vs. night) without making
transitions time-inhomogeneous — keeping the HMM simple and sound.
"""

from __future__ import annotations

import math

import numpy as np

from common.db import session_scope
from common.models import CongestionScore

FEATURE_NAMES = ["impact_score", "violation_count", "speed_drop_percent", "hour_sin", "hour_cos"]


def _row_to_features(r: CongestionScore) -> list[float]:
    hour = r.timestamp.hour + r.timestamp.minute / 60.0
    angle = 2 * math.pi * hour / 24.0
    return [r.impact_score, float(r.violation_count), r.speed_drop_percent, math.sin(angle), math.cos(angle)]


def list_zones() -> list[str]:
    with session_scope() as db:
        return [z[0] for z in db.query(CongestionScore.zone_id).distinct().all()]


def zone_matrix(zone_id: str, limit: int | None = None):
    """Return (X, timestamps) for one zone, oldest-first."""
    with session_scope() as db:
        q = db.query(CongestionScore).filter_by(zone_id=zone_id).order_by(CongestionScore.timestamp.asc())
        rows = q.all()
    if limit is not None:
        rows = rows[-limit:]
    X = np.array([_row_to_features(r) for r in rows], dtype=float)
    ts = [r.timestamp for r in rows]
    return X, ts


def training_matrix(min_len: int = 8):
    """Concatenated X with per-zone `lengths` (hmmlearn format), skipping short zones."""
    X_parts, lengths, zones = [], [], []
    for z in list_zones():
        X, _ = zone_matrix(z)
        if len(X) >= min_len:
            X_parts.append(X)
            lengths.append(len(X))
            zones.append(z)
    if not X_parts:
        raise RuntimeError("no zones with enough history — seed congestion_scores first")
    return np.vstack(X_parts), lengths, zones
