import json
from typing import Any, Optional
import redis.asyncio as aioredis
from shared.config.settings import settings


class RedisClient:
    def __init__(self):
        self.client = None

    async def init(self):
        self.client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        if not self.client:
            return None
        return await self.client.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if not self.client:
            return
        await self.client.set(key, json.dumps(value, default=str), ex=ttl)

    async def delete(self, key: str) -> None:
        if not self.client:
            return
        await self.client.delete(key)

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        if not self.client:
            return
        await self.client.zadd(key, mapping)

    async def zrevrange(self, key: str, start: int, stop: int) -> list[Any]:
        if not self.client:
            return []
        return await self.client.zrevrange(key, start, stop, withscores=True)

    async def hset(self, key: str, mapping: dict) -> None:
        if not self.client:
            return
        await self.client.hset(key, mapping=mapping)

    async def hgetall(self, key: str) -> dict:
        if not self.client:
            return {}
        return await self.client.hgetall(key)

    async def incr(self, key: str) -> int:
        if not self.client:
            return 0
        return await self.client.incr(key)

    async def expire(self, key: str, ttl: int) -> None:
        if not self.client:
            return
        await self.client.expire(key, ttl)

    async def close(self) -> None:
        if self.client:
            await self.client.close()


redis_client = RedisClient()
