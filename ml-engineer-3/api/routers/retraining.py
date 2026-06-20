"""Retraining trigger endpoints — status + manual/threshold trigger."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import require_role
from api.schemas import RetrainStatus
from feedback_loop import trigger

router = APIRouter(prefix="/api/v1/ml/retraining", tags=["retraining"])


@router.get("/status", response_model=RetrainStatus)
def retrain_status(_role: str = Depends(require_role("admin", "reviewer", "operator"))):
    return trigger.status()


@router.post("/trigger")
def trigger_retrain(
    full: bool = False,
    _role: str = Depends(require_role("admin", "reviewer")),
):
    """Manual retrain. full=false (default) runs the GPU-safe dry pipeline
    (ingest+validate+version) so the dataset-version bump is demonstrable;
    full=true runs real YOLOv8 training."""
    return trigger.maybe_trigger(reason="manual", skip_train=not full)
