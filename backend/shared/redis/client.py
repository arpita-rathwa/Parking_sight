import asyncio
import json
import logging
from typing import Any, Optional

from shared.config.settings import settings

logger = logging.getLogger("redis-client")


class _MemoryCache:
    """In-memory fallback when Redis is not available."""
    def __init__(self):
        self._data: dict = {}
        self._locks: dict = {}

    async def get(self, key: str) -> Optional[str]:
        entry = self._data.get(key)
        if entry is None:
            return None
        val, expiry = entry
        if expiry and asyncio.get_event_loop().time() > expiry:
            del self._data[key]
            return None
        return val

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        import time
        expiry = time.time() + ttl if ttl else 0
        self._data[key] = (json.dumps(value, default=str) if not isinstance(value, str) else value, expiry)

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        pass

    async def zrevrange(self, key: str, start: int, stop: int) -> list[Any]:
        return []

    async def hset(self, key: str, mapping: dict) -> None:
        pass

    async def hgetall(self, key: str) -> dict:
        return {}

    async def incr(self, key: str) -> int:
        return 0

    async def expire(self, key: str, ttl: int) -> None:
        pass

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def close(self) -> None:
        self._data.clear()


class RedisClient:
    def __init__(self):
        self._redis = None
        self._memory = _MemoryCache()
        self._use_redis = False

    async def init(self):
        url = settings.REDIS_URL
        if not url or url == "redis://" or url == "redis://localhost:6379/0":
            logger.warning("REDIS_URL empty/not configured — using in-memory cache")
            return
        try:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(url, decode_responses=True)
            await self._redis.ping()
            self._use_redis = True
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning("Redis unavailable (%s) — using in-memory cache", e)

    @property
    def client(self):
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        if self._use_redis and self._redis:
            try:
                return await self._redis.get(key)
            except Exception:
                pass
        return await self._memory.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.set(key, json.dumps(value, default=str), ex=ttl)
                return
            except Exception:
                pass
        await self._memory.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.delete(key)
                return
            except Exception:
                pass
        await self._memory.delete(key)

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.zadd(key, mapping)
            except Exception:
                pass

    async def zrevrange(self, key: str, start: int, stop: int) -> list[Any]:
        if self._use_redis and self._redis:
            try:
                return await self._redis.zrevrange(key, start, stop, withscores=True)
            except Exception:
                pass
        return []

    async def hset(self, key: str, mapping: dict) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.hset(key, mapping=mapping)
            except Exception:
                pass

    async def hgetall(self, key: str) -> dict:
        if self._use_redis and self._redis:
            try:
                return await self._redis.hgetall(key)
            except Exception:
                pass
        return {}

    async def incr(self, key: str) -> int:
        if self._use_redis and self._redis:
            try:
                return await self._redis.incr(key)
            except Exception:
                pass
        return 0

    async def expire(self, key: str, ttl: int) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.expire(key, ttl)
            except Exception:
                pass

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()


redis_client = RedisClient()
