import logging
from enum import Enum
from typing import Optional

from shared.config.settings import settings
from shared.kafka.producer import circuit_breaker
from shared.utils.redis_client import redis_client

logger = logging.getLogger("dependencies")


class DependencyStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


DependencyReport = dict[str, dict[str, str | int | float]]


def check_postgres() -> DependencyStatus:
    from sqlalchemy import create_engine, text

    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
            connect_args={"connect_timeout": 2},
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return DependencyStatus.HEALTHY
    except Exception:
        logger.warning("Postgres health check failed")
        return DependencyStatus.DOWN


def check_redis() -> DependencyStatus:
    client = redis_client.get_client()
    if client is None:
        return DependencyStatus.DOWN
    try:
        client.ping()
        return DependencyStatus.HEALTHY
    except Exception:
        logger.warning("Redis health check failed")
        return DependencyStatus.DOWN


def check_kafka() -> DependencyStatus:
    if circuit_breaker.state.value == "open":
        return DependencyStatus.DOWN
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            max_block_ms=2000,
        )
        producer.close()
        return DependencyStatus.HEALTHY
    except Exception:
        logger.warning("Kafka health check failed")
        return DependencyStatus.DEGRADED


def get_dependency_report() -> DependencyReport:
    return {
        "postgres": {
            "status": check_postgres().value,
        },
        "redis": {
            "status": check_redis().value,
        },
        "kafka": {
            "status": check_kafka().value,
            "circuit_breaker_state": circuit_breaker.state.value,
        },
    }
