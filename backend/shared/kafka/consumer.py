import json
from typing import Callable, Any
from kafka import KafkaConsumer
from shared.config.settings import settings


def create_consumer(topic: str, group_id: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )


def consume_loop(consumer: KafkaConsumer, handler: Callable[[str, Any], None]) -> None:
    for msg in consumer:
        handler(msg.key, msg.value)
