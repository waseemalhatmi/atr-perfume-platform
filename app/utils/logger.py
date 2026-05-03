"""
app/utils/logger.py
===================
Structured JSON logging utility — Production-grade observability.

Usage:
    from app.utils.logger import get_logger
    log = get_logger(__name__)
    log.info("item_fetched", item_id=42, latency_ms=12.3)

All log records include:
  - timestamp (ISO-8601 UTC)
  - level
  - logger (module name)
  - message
  - trace_id  (from Flask request context if available)
  - any extra keyword arguments passed by the caller
"""

import json
import logging
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    """Formats every log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        # Core fields always present
        doc = {
            "ts":      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }

        # Attach trace_id from Flask request context when available
        try:
            from flask import g, has_request_context
            if has_request_context() and hasattr(g, "trace_id"):
                doc["trace_id"] = g.trace_id
        except Exception:
            pass

        # Any extra fields the caller passed via log.info("msg", extra={...})
        for key, val in record.__dict__.items():
            if key not in {
                "args", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno",
                "message", "module", "msecs", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "taskName", "thread", "threadName",
            }:
                doc[key] = val

        if record.exc_info:
            doc["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(doc, default=str, ensure_ascii=False)


class _StructuredLogger(logging.Logger):
    """Extends stdlib Logger with keyword-argument style calls."""

    def _log_with_extras(self, level: int, msg: str, kwargs: dict):
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        super().log(level, msg, extra=extra)

    def info(self, msg: str, *args, **kwargs):           # type: ignore[override]
        self._log_with_extras(logging.INFO,    msg, kwargs)

    def warning(self, msg: str, *args, **kwargs):        # type: ignore[override]
        self._log_with_extras(logging.WARNING,  msg, kwargs)

    def error(self, msg: str, *args, **kwargs):          # type: ignore[override]
        self._log_with_extras(logging.ERROR,    msg, kwargs)

    def critical(self, msg: str, *args, **kwargs):       # type: ignore[override]
        self._log_with_extras(logging.CRITICAL, msg, kwargs)

    def debug(self, msg: str, *args, **kwargs):          # type: ignore[override]
        self._log_with_extras(logging.DEBUG,    msg, kwargs)


def get_logger(name: str) -> _StructuredLogger:
    """
    Return a module-level structured logger.

    Example:
        log = get_logger(__name__)
        log.info("cache_hit", key="item:42", latency_ms=0.3)
    """
    logging.setLoggerClass(_StructuredLogger)
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False   # Don't double-log to root logger

    return logger  # type: ignore[return-value]
