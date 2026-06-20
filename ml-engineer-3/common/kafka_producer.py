"""Thin Kafka producer. No-ops (logs only) when KAFKA_BOOTSTRAP is unset so the
demo runs without a broker. The model.promoted event is how detection-service
(ML Eng 1) learns to hot-reload the new champion.
"""

from __future__ import annotations

import json

from common.config import get_settings
from common.logging import get_logger

log = get_logger("common.kafka")


class EventBus:
    def __init__(self) -> None:
        self.s = get_settings()
        self._producer = None
        if self.s.kafka_bootstrap:
            from kafka import KafkaProducer  # lazy

            self._producer = KafkaProducer(
                bootstrap_servers=self.s.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode(),
            )

    def emit(self, topic: str, event: dict) -> None:
        if self._producer is None:
            log.info("event_emitted_noop", topic=topic, event=event)
            return
        self._producer.send(topic, event)
        self._producer.flush()
        log.info("event_emitted", topic=topic, event_keys=list(event))


def emit_model_promoted(version: str, weights_uri: str, metrics: dict) -> None:
    """Schema for model.promoted (owned by ML Eng 3, consumed by detection-service)."""
    EventBus().emit(
        get_settings().topic_model_promoted,
        {
            "event": "model.promoted",
            "schema_version": 1,
            "model_version": version,
            "weights_uri": weights_uri,
            "metrics": {k: metrics.get(k) for k in ("map50", "map5095", "precision", "recall")},
        },
    )


def emit_officer_feedback(payload: dict) -> None:
    """Schema for officer.feedback (see common/schemas/officer_feedback.json).

    In production officer-app-api (Backend) emits this on the unresolvable status
    transition; here we also emit it from our submit endpoint so the loop is
    demonstrable without the Backend producer in place yet.
    """
    required = {"event", "schema_version", "feedback_id", "violation_id", "officer_id", "status"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"officer.feedback missing required fields: {missing}")
    EventBus().emit(get_settings().topic_officer_feedback, payload)


def emit_hotspot_predictions(predictions: list[dict]) -> None:
    """Schema for hotspot.predictions (owned by ML Eng 3, consumed by dashboard /
    notification-service for the predictive heatmap overlay)."""
    EventBus().emit(
        get_settings().topic_hotspot_predictions,
        {
            "event": "hotspot.predictions",
            "schema_version": 1,
            "horizon_minutes": get_settings().hmm_bin_minutes,
            "zones": predictions,
        },
    )
