"""Allowlisted JSON logs; arbitrary extras and exception messages are never serialized."""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
SAFE_FIELDS = frozenset(
    {
        "tenant_id",
        "actor_id",
        "operation_id",
        "event_id",
        "workflow_id",
        "attempt",
        "duration_ms",
        "status_code",
        "error_code",
        "provider",
        "release",
        "environment",
    }
)


def request_id(value: str | None) -> str:
    try:
        return str(UUID(value)) if value else str(uuid4())
    except (ValueError, TypeError, AttributeError):
        return str(uuid4())


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "severity": record.levelname,
            "service": record.name,
            "event": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        for field in SAFE_FIELDS:
            value = getattr(record, field, None)
            if isinstance(value, str | int | float | bool):
                data[field] = value
            elif isinstance(value, UUID):
                data[field] = str(value)
        if record.exc_info and record.exc_info[0]:
            data["exception_type"] = record.exc_info[0].__name__
        return json.dumps(data, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("meu_braco_direito")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
