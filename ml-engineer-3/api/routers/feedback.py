"""Officer-facing endpoints: submit feedback + upload photo evidence."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.deps import require_role
from api.schemas import FeedbackCreate, FeedbackResponse
from feedback_loop import service

router = APIRouter(prefix="/api/v1/officer", tags=["officer-feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(body: FeedbackCreate, _role: str = Depends(require_role("officer", "admin"))):
    try:
        return service.submit_feedback(**body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/feedback/{feedback_id}/evidence")
async def upload_evidence(
    feedback_id: str,
    file: UploadFile = File(...),
    _role: str = Depends(require_role("officer", "admin")),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    try:
        return service.attach_evidence(feedback_id, data, file.content_type or "image/jpeg")
    except ValueError as e:
        raise HTTPException(400, str(e))
