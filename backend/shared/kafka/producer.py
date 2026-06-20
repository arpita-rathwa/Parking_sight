import json
from typing import Any, Optional

from kafka import KafkaProducer

from shared.config.settings import settings
from shared.kafka.circuit_breaker import CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=settings.KAFKA_CIRCUIT_BREAKER_THRESHOLD,
    cooldown_seconds=settings.KAFKA_CIRCUIT_BREAKER_COOLDOWN,
)


class ParkSightProducer:
    def __init__(self):
        self._producer: KafkaProducer | None = None

    def _ensure_connected(self) -> None:
        if self._producer is not None:
            return
        self._producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: str(k).encode("utf-8") if k else None,
            acks="all",
            retries=3,
        )

    def send(self, topic: str, key: Optional[str], value: dict[str, Any]) -> bool:
        if not circuit_breaker.try_request():
            return False
        try:
            self._ensure_connected()
            self._producer.send(topic, key=key, value=value)
            self._producer.flush()
            circuit_breaker.on_success()
            return True
        except Exception:
            circuit_breaker.on_failure()
            return False

    def flush(self) -> None:
        if self._producer is not None:
            try:
                self._producer.flush()
            except Exception:
                pass

    def close(self) -> None:
        if self._producer is not None:
            try:
                self._producer.close()
            except Exception:
                pass
            self._producer = None


producer = ParkSightProducer()
