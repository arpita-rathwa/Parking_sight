"""Reviewer-facing endpoints (ML Engineer 1): view queue, approve, reject."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import require_reviewer
from api.schemas import ApproveRequest, RejectRequest, ReviewItem
from feedback_loop import review

router = APIRouter(prefix="/api/v1/review", tags=["review"])


@router.get("/queue", response_model=list[ReviewItem])
def view_queue(status: str = "pending", _role: str = Depends(require_reviewer())):
    return review.list_queue(status=status)


@router.get("/queue/{review_id}", response_model=ReviewItem)
def view_item(review_id: str, _role: str = Depends(require_reviewer())):
    item = review.get_item(review_id)
    if not item:
        raise HTTPException(404, "review item not found")
    return item


@router.post("/queue/{review_id}/approve", response_model=ReviewItem)
def approve_item(review_id: str, body: ApproveRequest, role: str = Depends(require_reviewer())):
    try:
        return review.approve(
            review_id,
            reviewer_id=role,
            class_id=body.class_id,
            bbox=body.bbox.model_dump() if body.bbox else None,
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/queue/{review_id}/reject", response_model=ReviewItem)
def reject_item(review_id: str, body: RejectRequest, role: str = Depends(require_reviewer())):
    try:
        return review.reject(review_id, reviewer_id=role, notes=body.notes)
    except ValueError as e:
        raise HTTPException(400, str(e))
