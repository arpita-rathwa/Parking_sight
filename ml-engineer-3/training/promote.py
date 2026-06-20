"""Stage 6 — Promote (champion/challenger gate) + rollback.

A candidate is promoted only if ALL hold:
  1. map50 >= PROMOTION_MIN_MAP50            (absolute quality floor)
  2. map50 >= champion.map50 + MIN_DELTA      (must actually be better)
  3. no per-class mAP50 regression > TOLERANCE vs champion  (don't trade a class away)

First-ever model only needs to clear the floor (no champion to beat).
On promotion we emit model.promoted so detection-service hot-reloads.
"""

from __future__ import annotations

from dataclasses import dataclass

from common.config import get_settings
from common.db import session_scope
from common.kafka_producer import emit_model_promoted
from common.logging import get_logger
from common.models import ModelRegistry
from training.registry import get_champion_metrics, set_champion

log = get_logger("training.promote")


@dataclass
class GateResult:
    promote: bool
    reasons: list[str]


def evaluate_gate(candidate: dict, champion: dict | None) -> GateResult:
    s = get_settings()
    reasons: list[str] = []

    if candidate["map50"] < s.promotion_min_map50:
        reasons.append(f"below floor: map50 {candidate['map50']:.4f} < {s.promotion_min_map50}")
        return GateResult(False, reasons)

    if champion is None:
        reasons.append("first model — promoted by clearing the floor")
        return GateResult(True, reasons)

    if candidate["map50"] < champion["map50"] + s.promotion_min_delta:
        reasons.append(
            f"no improvement: map50 {candidate['map50']:.4f} < "
            f"champion {champion['map50']:.4f} + {s.promotion_min_delta}"
        )
        return GateResult(False, reasons)

    # Only compare classes that were actually measured in BOTH evaluations.
    # A class absent from the candidate's metrics means it had no val instances
    # this cycle (common with imbalanced real data) — we cannot call that a
    # regression, so we skip it rather than treating it as 0.0.
    cand_per_class = candidate.get("per_class") or {}
    for cls, champ_ap in (champion.get("per_class") or {}).items():
        if cls not in cand_per_class:
            continue
        cand_ap = cand_per_class[cls]
        if champ_ap - cand_ap > s.promotion_per_class_tolerance:
            reasons.append(f"class regression '{cls}': {cand_ap:.3f} vs champion {champ_ap:.3f}")
            return GateResult(False, reasons)

    reasons.append(f"improved map50 {champion['map50']:.4f} -> {candidate['map50']:.4f}")
    return GateResult(True, reasons)


def promote_if_better(version: str, metrics: dict) -> GateResult:
    result = evaluate_gate(metrics, get_champion_metrics())
    if result.promote:
        set_champion(version)
        with session_scope() as db:
            champ = db.query(ModelRegistry).filter_by(version=version).one()
            emit_model_promoted(version, champ.weights_uri, metrics)
    log.info("promotion_decision", version=version, promote=result.promote, reasons=result.reasons)
    return result


def rollback(to_version: str) -> None:
    """Manual rollback: restore a prior version as champion + re-emit promoted."""
    set_champion(to_version)
    with session_scope() as db:
        target = db.query(ModelRegistry).filter_by(version=to_version).one()
        emit_model_promoted(to_version, target.weights_uri, target.metrics or {})
    log.info("rollback_done", version=to_version)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3 and sys.argv[1] == "rollback":
        rollback(sys.argv[2])
