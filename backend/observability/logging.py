"""Structured logging setup with request correlation fields."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from observability.context import get_request_id, get_trace_id


class JsonLogFormatter(logging.Formatter):
    """Emit JSON log lines for easier backend observability."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "trace_id": get_trace_id(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_structured_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    has_json_handler = False
    for handler in root.handlers:
        if isinstance(handler.formatter, JsonLogFormatter):
            has_json_handler = True
            break

    if has_json_handler:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root.handlers = [handler]
