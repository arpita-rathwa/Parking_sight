"""Retraining trigger.

A retrain fires when EITHER:
  * approved relabels since the last successful run >= FEEDBACK_RETRAIN_THRESHOLD, OR
  * a manual request is made.

"Approved since last run" is counted by comparing each approved item's decided_at
to the start of the most recent successful/dry-run retraining run — no extra table.
"""

from __future__ import annotations

from common.config import get_settings
from common.db import session_scope
from common.logging import get_logger
from common.models import LabelReviewQueue, RetrainingRun

log = get_logger("feedback.trigger")

_SUCCESS_STATES = ("success", "success_dry_run")


def _last_successful_run_start():
    with session_scope() as db:
        run = (
            db.query(RetrainingRun)
            .filter(RetrainingRun.status.in_(_SUCCESS_STATES))
            .order_by(RetrainingRun.started_at.desc())
            .first()
        )
        return run.started_at if run else None


def approved_since_last_retrain() -> int:
    cutoff = _last_successful_run_start()
    with session_scope() as db:
        q = db.query(LabelReviewQueue).filter(LabelReviewQueue.status == "approved")
        if cutoff is not None:
            q = q.filter(LabelReviewQueue.decided_at > cutoff)
        return q.count()


def status() -> dict:
    s = get_settings()
    pending_approved = approved_since_last_retrain()
    return {
        "approved_since_last_retrain": pending_approved,
        "threshold": s.feedback_retrain_threshold,
        "due": pending_approved >= s.feedback_retrain_threshold,
        "last_retrain_started": _last_successful_run_start(),
    }


def maybe_trigger(reason: str = "feedback_threshold", skip_train: bool = True) -> dict:
    """Trigger a retrain if due (or always, if reason == 'manual').
    Defaults to skip_train=True so demos/API calls are GPU-safe; pass
    skip_train=False for the real training run."""
    st = status()
    if reason != "manual" and not st["due"]:
        log.info("retrain_not_due", **{k: st[k] for k in ("approved_since_last_retrain", "threshold")})
        return {"triggered": False, **st}

    from training.pipeline import run as run_pipeline

    log.info(
        "retrain_triggering", reason=reason, skip_train=skip_train, approved=st["approved_since_last_retrain"]
    )
    result = run_pipeline(
        trigger=reason if reason == "manual" else "feedback_threshold", skip_train=skip_train
    )
    return {"triggered": True, "reason": reason, "run": result, **status()}
