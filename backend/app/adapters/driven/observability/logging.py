from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Any

from app.adapters.driving.web.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def kv(**values: Any) -> str:
    """Build stable key=value log suffix, skipping nulls."""
    parts: list[str] = []
    sensitive_keys = ("token", "secret", "password", "authorization", "cookie")
    for key in sorted(values):
        value = values[key]
        if value is None:
            continue
        if any(marker in key.lower() for marker in sensitive_keys):
            parts.append(f"{key}=<redacted>")
            continue
        text = str(value).replace("\n", "\\n")
        parts.append(f"{key}={text}")
    return " ".join(parts)


def configure_logging(level: str) -> None:
    normalized_level = level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {
                    "()": "app.adapters.driven.observability.logging.RequestIdFilter",
                }
            },
            "formatters": {
                "standard": {"format": ("%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s")}
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "level": normalized_level,
                    "formatter": "standard",
                    "filters": ["request_id"],
                }
            },
            "root": {"level": normalized_level, "handlers": ["default"]},
            "loggers": {
                "uvicorn.access": {"level": "INFO", "propagate": True},
                "uvicorn.error": {"level": normalized_level, "propagate": True},
                "sqlalchemy.engine": {"level": "WARNING", "propagate": True},
            },
        }
    )
