import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from shared.config.settings import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        rate_key = f"{client_ip}:{path}"

        now = time.time()
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        max_requests = self._get_limit_for_path(path)

        self.requests[rate_key] = [t for t in self.requests[rate_key] if now - t < window]

        if len(self.requests[rate_key]) >= max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        self.requests[rate_key].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max_requests - len(self.requests[rate_key]))
        response.headers["X-RateLimit-Reset"] = str(int(now + window))
        return response

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
