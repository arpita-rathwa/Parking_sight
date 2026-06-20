"""Review service — the reviewer-facing half (ML Engineer 1).

approve():  write the (image, label) into the training staging set so Phase 2's
            ingest picks it up on the next retrain, mark approved.
reject():   archive, no dataset change.

The approval is what makes the loop "continuous learning": an approved label is
physically added to datasets/staging/ and becomes part of the next dataset version.
"""

from __future__ import annotations

import datetime as dt

from common.config import get_settings
from common.db import session_scope
from common.logging import get_logger
from common.models import LabelReviewQueue
from common.storage import Storage

log = get_logger("feedback.review")


def list_queue(status: str = "pending", limit: int = 100) -> list[dict]:
    with session_scope() as db:
        rows = (
            db.query(LabelReviewQueue)
            .filter_by(status=status)
            .order_by(LabelReviewQueue.created_at.asc())
            .limit(limit)
            .all()
        )
        return [_to_dict(r) for r in rows]


def get_item(review_id: str) -> dict | None:
    with session_scope() as db:
        row = db.query(LabelReviewQueue).filter_by(id=review_id).one_or_none()
        return _to_dict(row) if row else None


def approve(
    review_id: str,
    reviewer_id: str,
    class_id: int | None = None,
    bbox: dict | None = None,
    notes: str | None = None,
) -> dict:
    """Approve a relabel. class_id/bbox default to the proposed values.
    Writes the labeled sample into datasets/staging/ for the next retrain."""
    s = get_settings()
    storage = Storage()

    with session_scope() as db:
        item = db.query(LabelReviewQueue).filter_by(id=review_id).one()
        if item.status != "pending":
            raise ValueError(f"review item already {item.status}")

        final_class = class_id if class_id is not None else item.proposed_class_id
        if final_class is None or not (0 <= final_class < len(s.classes)):
            raise ValueError("a valid corrected class_id (0..N-1) is required to approve")
        final_bbox = bbox or item.proposed_bbox or {"cx": 0.5, "cy": 0.5, "w": 0.6, "h": 0.6}

        # copy image -> staging/images, write YOLO label -> staging/labels
        img_bytes = storage.get_bytes(s.s3_bucket_frames, item.image_s3_key)
        stem = f"feedback_{item.id}"
        storage.put_bytes(s.s3_bucket_datasets, f"staging/images/{stem}.jpg", img_bytes)
        label_line = (
            f"{final_class} {final_bbox['cx']:.6f} {final_bbox['cy']:.6f} "
            f"{final_bbox['w']:.6f} {final_bbox['h']:.6f}"
        )
        storage.put_bytes(s.s3_bucket_datasets, f"staging/labels/{stem}.txt", label_line.encode())

        item.status = "approved"
        item.reviewer_id = reviewer_id
        item.corrected_class_id = final_class
        item.corrected_bbox = final_bbox
        item.dataset_image_key = f"staging/images/{stem}.jpg"
        item.decision_notes = notes
        item.decided_at = dt.datetime.now(dt.timezone.utc)
        result = _to_dict(item)

    log.info(
        "review_approved",
        review_id=review_id,
        reviewer_id=reviewer_id,
        class_id=result["corrected_class_id"],
        dataset_key=result["dataset_image_key"],
    )
    return result


def reject(review_id: str, reviewer_id: str, notes: str | None = None) -> dict:
    with session_scope() as db:
        item = db.query(LabelReviewQueue).filter_by(id=review_id).one()
        if item.status != "pending":
            raise ValueError(f"review item already {item.status}")
        item.status = "rejected"
        item.reviewer_id = reviewer_id
        item.decision_notes = notes
        item.decided_at = dt.datetime.now(dt.timezone.utc)
        result = _to_dict(item)
    log.info("review_rejected", review_id=review_id, reviewer_id=reviewer_id)
    return result


def _to_dict(r: LabelReviewQueue) -> dict:
    s = get_settings()
    return {
        "id": r.id,
        "feedback_id": r.feedback_id,
        "violation_id": r.violation_id,
        "image_s3_key": r.image_s3_key,
        "proposed_class_id": r.proposed_class_id,
        "proposed_class": s.classes[r.proposed_class_id] if r.proposed_class_id is not None else None,
        "proposed_bbox": r.proposed_bbox,
        "status": r.status,
        "reviewer_id": r.reviewer_id,
        "corrected_class_id": r.corrected_class_id,
        "corrected_class": s.classes[r.corrected_class_id] if r.corrected_class_id is not None else None,
        "dataset_image_key": r.dataset_image_key,
        "decision_notes": r.decision_notes,
        "created_at": r.created_at,
        "decided_at": r.decided_at,
    }
