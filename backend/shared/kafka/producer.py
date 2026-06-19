import json
from typing import Any, Optional
from kafka import KafkaProducer
from shared.config.settings import settings


class ParkSightProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: str(k).encode("utf-8") if k else None,
            acks="all",
            retries=3,
        )

    def send(self, topic: str, key: Optional[str], value: dict[str, Any]) -> None:
        self.producer.send(topic, key=key, value=value)
        self.producer.flush()

    def close(self) -> None:
        self.producer.close()


producer = ParkSightProducer()
