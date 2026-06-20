import logging
import time

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from shared.config.settings import settings
from shared.utils.redis_client import redis_client

logger = logging.getLogger("rate_limiter")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        rate_key = f"ratelimit:{client_ip}:{path}"
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        max_requests = self._get_limit_for_path(path)

        remaining, reset = self._check_rate_limit(rate_key, max_requests, window)
        if remaining is None:
            return await call_next(request)

        if remaining < 0:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(max(1, reset - int(time.time()))),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
        return response

    def _check_rate_limit(
        self, key: str, max_requests: int, window: int
    ) -> tuple[int, int]:
        client = redis_client.get_client()
        if client is None:
            return None, None

        now = int(time.time())
        window_start = now - window
        try:
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window + 5)
            pipe.zrangebyscore(key, window_start, now)
            pipe.execute()

            count = client.zcard(key)
            reset = window_start + window
            remaining = max_requests - count

            return remaining, reset
        except Exception:
            logger.exception("Redis rate limit check failed, allowing request")
            return None, None

    def _get_limit_for_path(self, path: str) -> int:
        if "detect" in path:
            return 100
        if "officer" in path:
            return settings.OFFICER_APP_RATE_LIMIT
        if "analytics" in path:
            return settings.ANALYTICS_RATE_LIMIT
        if "admin" in path:
            return 10
        if "login" in path:
            return settings.LOGIN_RATE_LIMIT_ATTEMPTS
        return settings.RATE_LIMIT_REQUESTS
