"""Feedback service — the officer-facing half of the loop.

Flow:
  submit_feedback()  -> create FeedbackSubmission (resolved | unresolvable)
  attach_evidence()  -> store photo, emit officer.feedback, hand off to review

In demo mode (no KAFKA_BOOTSTRAP) attach_evidence processes the event inline so
the review item appears immediately; in production the Kafka consumer
(feedback_loop/consumer.py) does that step. Same handler either way.
"""

from __future__ import annotations

import datetime as dt

from common.config import get_settings
from common.db import session_scope
from common.kafka_producer import emit_officer_feedback
from common.logging import get_logger
from common.models import FeedbackSubmission
from common.storage import Storage

log = get_logger("feedback.service")


def submit_feedback(
    *,
    violation_id: str,
    officer_id: str,
    status: str,
    camera_id: str | None = None,
    zone_id: str | None = None,
    reason: str | None = None,
    proposed_class: str | None = None,
    crop_s3_key: str | None = None,
) -> dict:
    if status not in ("resolved", "unresolvable"):
        raise ValueError("status must be 'resolved' or 'unresolvable'")
    with session_scope() as db:
        fb = FeedbackSubmission(
            violation_id=violation_id,
            officer_id=officer_id,
            status=status,
            camera_id=camera_id,
            zone_id=zone_id,
            reason=reason,
            proposed_class=proposed_class,
            crop_s3_key=crop_s3_key,
        )
        db.add(fb)
        db.flush()
        fb_id = fb.id
    next_action = "upload_evidence" if status == "unresolvable" else "none"
    log.info("feedback_submitted", feedback_id=fb_id, status=status, violation_id=violation_id)
    return {"feedback_id": fb_id, "status": status, "next_action": next_action}


def attach_evidence(feedback_id: str, image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    s = get_settings()
    storage = Storage()
    today = dt.datetime.now(dt.timezone.utc)
    ext = "png" if "png" in content_type else "jpg"
    photo_key = f"evidence/{today:%Y/%m/%d}/{feedback_id}.{ext}"
    storage.put_bytes(s.s3_bucket_frames, photo_key, image_bytes)

    with session_scope() as db:
        fb = db.query(FeedbackSubmission).filter_by(id=feedback_id).one()
        if fb.status != "unresolvable":
            raise ValueError("evidence only applies to 'unresolvable' feedback")
        fb.photo_s3_key = photo_key
        fb.event_emitted = True
        event = {
            "event": "officer.feedback",
            "schema_version": 1,
            "feedback_id": fb.id,
            "violation_id": fb.violation_id,
            "camera_id": fb.camera_id,
            "zone_id": fb.zone_id,
            "officer_id": fb.officer_id,
            "status": fb.status,
            "reason": fb.reason,
            "proposed_class": fb.proposed_class,
            "photo_s3_key": fb.photo_s3_key,
            "crop_s3_key": fb.crop_s3_key,
            "timestamp": today.isoformat(),
        }

    emit_officer_feedback(event)

    # In demo (no broker) run the consumer handler inline so the review item exists now.
    if not s.kafka_bootstrap:
        from feedback_loop.consumer import process_officer_feedback

        process_officer_feedback(event)

    log.info("evidence_attached", feedback_id=feedback_id, photo_key=photo_key)
    return {"feedback_id": feedback_id, "photo_s3_key": photo_key, "event": "officer.feedback emitted"}
