"""officer.feedback consumer.

`process_officer_feedback(event)` is the handler: it turns an unresolvable
feedback event into a pending LabelReviewQueue item. It is called inline in demo
mode and by the Kafka consumer loop in production — single code path.
"""

from __future__ import annotations

from common.config import get_settings
from common.db import session_scope
from common.logging import get_logger
from common.models import LabelReviewQueue

log = get_logger("feedback.consumer")


def process_officer_feedback(event: dict) -> str | None:
    """Create a pending review item from an unresolvable feedback event.
    Returns the review item id, or None if the event needs no relabeling."""
    if event.get("status") != "unresolvable":
        log.info("feedback_ignored_for_ml", feedback_id=event.get("feedback_id"), status=event.get("status"))
        return None

    image_key = event.get("photo_s3_key") or event.get("crop_s3_key")
    if not image_key:
        log.info("feedback_no_image_skipped", feedback_id=event.get("feedback_id"))
        return None

    s = get_settings()
    proposed_class_id = (
        s.class_to_id.get(event.get("proposed_class")) if event.get("proposed_class") else None
    )

    with session_scope() as db:
        item = LabelReviewQueue(
            feedback_id=event["feedback_id"],
            violation_id=event["violation_id"],
            image_s3_key=image_key,
            proposed_class_id=proposed_class_id,
            proposed_bbox={"cx": 0.5, "cy": 0.5, "w": 0.6, "h": 0.6},  # MVP default; reviewer adjusts in CVAT
            status="pending",
        )
        db.add(item)
        db.flush()
        item_id = item.id
    log.info("review_item_enqueued", review_id=item_id, feedback_id=event["feedback_id"])
    return item_id


def run_consumer() -> None:  # pragma: no cover (production entrypoint)
    """Long-running Kafka consumer for officer.feedback (production)."""
    import json

    from kafka import KafkaConsumer

    s = get_settings()
    consumer = KafkaConsumer(
        s.topic_officer_feedback,
        bootstrap_servers=s.kafka_bootstrap,
        value_deserializer=lambda v: json.loads(v.decode()),
        group_id="ml-feedback-loop",
        auto_offset_reset="earliest",
    )
    log.info("consumer_started", topic=s.topic_officer_feedback)
    for msg in consumer:
        try:
            process_officer_feedback(msg.value)
        except Exception as e:  # noqa: BLE001
            log.error("consumer_handler_failed", error=str(e))


if __name__ == "__main__":
    run_consumer()
