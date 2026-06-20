"""Seed synthetic congestion_scores with realistic daily regimes so the HMM has a
clear signal to learn (calm nights, building mornings, congested rush hours, and
occasional critical spikes). Some zones are 'hotter' than others.

    python scripts/seed_hmm_data.py --zones 6 --days 7
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import random

from common.db import init_db, session_scope
from common.logging import get_logger
from common.models import CongestionScore

log = get_logger("scripts.seed_hmm")


def _daily_factor(hour: float) -> float:
    """Two rush peaks (~9:00 and ~18:00), quiet at night."""
    morning = math.exp(-((hour - 9) ** 2) / (2 * 1.6**2))
    evening = math.exp(-((hour - 18) ** 2) / (2 * 1.8**2))
    return 0.1 + 0.9 * max(morning, evening)


def seed(zones: int = 6, days: int = 7, bin_minutes: int = 30, seed_val: int = 7, end_hour: int = 18) -> None:
    """Seed `days` of history, with the final day truncated at `end_hour` so the
    forecast 'now' sits at the evening rush — hot zones light up, calm zones don't."""
    init_db()
    rng = random.Random(seed_val)
    start = dt.datetime(2026, 6, 12, 0, 0, tzinfo=dt.timezone.utc)
    bins_per_day = 24 * 60 // bin_minutes
    last_day_bins = end_hour * 60 // bin_minutes
    rows = []
    for z in range(zones):
        hotness = 0.5 + 1.3 * (z / max(1, zones - 1))  # zone_00 calm -> zone_N hot
        for d in range(days):
            n_bins = last_day_bins if d == days - 1 else bins_per_day
            for b in range(n_bins):
                ts = start + dt.timedelta(days=d, minutes=b * bin_minutes)
                hour = ts.hour + ts.minute / 60.0
                base = _daily_factor(hour) * hotness
                spike = 1.8 if rng.random() < 0.02 else 1.0  # rare critical incident
                load = base * spike

                violations = max(0, int(rng.gauss(load * 9, 2)))
                speed_drop = max(0.0, min(80.0, rng.gauss(load * 35, 6)))
                impact = max(0.0, min(1.0, load * 0.55 + rng.gauss(0, 0.04)))
                rows.append(
                    CongestionScore(
                        zone_id=f"zone_{z:02d}",
                        timestamp=ts,
                        speed_drop_percent=round(speed_drop, 2),
                        violation_count=violations,
                        impact_score=round(impact, 4),
                    )
                )
    with session_scope() as db:
        db.add_all(rows)
    log.info("hmm_data_seeded", zones=zones, days=days, rows=len(rows))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", type=int, default=6)
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    seed(a.zones, a.days)
