from shared.config.settings import settings


def test_queue_settings():
    assert settings.PRIORITY_QUEUE_CACHE_TTL == 300
    assert settings.MAX_QUEUE_SIZE == 1000
