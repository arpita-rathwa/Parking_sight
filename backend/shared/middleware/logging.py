import time
import uuid
import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("parksight")
logger.setLevel(logging.INFO)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        request.state.trace_id = trace_id
        start = time.time()

        response = await call_next(request)

        elapsed = time.time() - start
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": request.app.title if hasattr(request.app, "title") else "unknown",
            "level": "INFO",
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(elapsed * 1000, 2),
            "ip": request.client.host if request.client else None,
        }
        logger.info(json.dumps(log_entry, default=str))
        response.headers["X-Trace-ID"] = trace_id
        return response
