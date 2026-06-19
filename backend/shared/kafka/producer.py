import json
from typing import Any, Optional

from kafka import KafkaProducer

from shared.config.settings import settings


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
        try:
            self._ensure_connected()
            self._producer.send(topic, key=key, value=value)
            self._producer.flush()
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._producer is not None:
            try:
                self._producer.close()
            except Exception:
                pass
            self._producer = None


producer = ParkSightProducer()
