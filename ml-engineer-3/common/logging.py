"""Structured JSON logging — matches the layer-12 log format in the 16-layer doc.

Usage:
    from common.logging import get_logger
    log = get_logger("training.pipeline")
    log.info("dataset_versioned", version="ds_20260619", n_images=412)
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "service": "ml-platform",
            "logger": record.name,
            "level": record.levelname,
            "event": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class _Adapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.pop("extra", {})
        fields = {k: v for k, v in kwargs.items() if k not in ("exc_info", "stack_info", "stacklevel")}
        for k in list(fields):
            kwargs.pop(k, None)
        kwargs["extra"] = {"extra_fields": {**extra, **fields}, "trace_id": self.extra.get("trace_id")}
        return msg, kwargs


def get_logger(name: str, trace_id: str | None = None) -> _Adapter:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return _Adapter(logger, {"trace_id": trace_id or uuid.uuid4().hex[:12]})
