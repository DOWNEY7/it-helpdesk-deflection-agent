"""
Structured JSON logger — wraps structlog with Pydantic log event models.
Every call writes a validated JSON object to both stdout and the log file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import structlog

from app.config import get_settings
from app.monitoring.log_schema import BaseLogEvent


def _ensure_log_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    """
    Configure structlog for JSON output.
    Called once at application startup from main.py.
    """

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,

            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )


class StructuredLogger:
    """
    Application logger that:
      1. Validates events through Pydantic log schemas.
      2. Writes JSON to stdout (picked up by container runtime / Azure Monitor).
      3. Appends JSON lines to the configured log file.
    """

    def __init__(self) -> None:
        self._log = structlog.get_logger()
        self._settings = get_settings()
        _ensure_log_dir(self._settings.app_log_path)

    def _write_to_file(self, path: Path, data: dict[str, Any]) -> None:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, default=str) + "\n")
        except OSError:
            pass  # never let logging break the request

    def emit(self, event: BaseLogEvent) -> None:
        """Validate and emit any typed log event."""
        data = event.model_dump(mode="json")
        level = data.get("level", "INFO").lower()
        log_fn = getattr(self._log, level, self._log.info)
        log_fn(event.event, **{k: v for k, v in data.items() if k != "event"})
        self._write_to_file(self._settings.app_log_path, data)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log.error(msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log.debug(msg, **kwargs)


# Module-level singleton
logger = StructuredLogger()
