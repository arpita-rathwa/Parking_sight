"""End-to-end HMM pre-staging demo — the forecasting showpiece.

    python scripts/demo_hmm.py --zones 6 --days 7

Seeds synthetic congestion history -> trains the HMM -> forecasts every zone ->
prints a ranked hotspot table + one plain-language explanation -> writes the
three demo figures to ./hmm_reports/.
"""

from __future__ import annotations

import argparse

from common.db import init_db
from hmm_prediction import features, infer, train_hmm, visualize
from scripts.seed_hmm_data import seed


def run(zones: int, days: int, retrain: bool) -> None:
    init_db()
    if retrain or not features.list_zones():
        print(f"seeding {zones} zones x {days} days of congestion history...")
        seed(zones=zones, days=days)

    print("training HMM (calm / building / congested / critical)...")
    infer.reset_cache()
    meta = train_hmm.train()
    print(
        f"  trained on {meta['n_observations']} obs across {meta['n_zones']} zones | "
        f"log-likelihood={meta['log_likelihood']:.0f}\n"
    )

    preds = infer.forecast_all(persist=True)
    print("=== HOTSPOT FORECAST (next 30 min), ranked by risk ===")
    print(f"{'zone':10} {'current':12} {'predicted':12} {'hotspot%':9} {'risk':6}")
    for p in preds:
        print(
            f"{p['zone_id']:10} {p['current_state_name']:12} {p['predicted_state_name']:12} "
            f"{p['hotspot_probability'] * 100:7.0f}%  {p['risk_score']:.2f}"
        )

    top = preds[0]
    print(f"\nEXPLANATION (top zone {top['zone_id']}):\n  {top['explanation']}\n")

    paths = visualize.generate_all(sample_zone=preds[0]["zone_id"])
    print("figures written:")
    for p in paths:
        print("  -", p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", type=int, default=6)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--retrain", action="store_true", help="reseed + retrain even if data exists")
    a = ap.parse_args()
    run(a.zones, a.days, a.retrain)
