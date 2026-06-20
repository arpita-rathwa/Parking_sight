import logging
from typing import Optional

import redis

from shared.config.settings import settings

logger = logging.getLogger("redis.client")


class RedisClient:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def get_client(self) -> Optional[redis.Redis]:
        if self._client is not None:
            try:
                self._client.ping()
                return self._client
            except (redis.ConnectionError, redis.TimeoutError):
                logger.warning("Redis ping failed, reconnecting...")
                self._client = None
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
            )
            self._client.ping()
            return self._client
        except Exception:
            logger.exception("Failed to connect to Redis")
            self._client = None
            return None

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None


redis_client = RedisClient()
