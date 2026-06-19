from shared.config.settings import settings
from shared.kafka.topics import KAFKA_TOPICS


def test_settings():
    assert settings.APP_NAME == "ParkSight"
    assert settings.DETECTION_CONFIDENCE_THRESHOLD == 0.5


def test_kafka_topics():
    assert "violations_raw" in KAFKA_TOPICS
    assert KAFKA_TOPICS["violations_raw"] == "violations.raw"
