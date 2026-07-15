"""
Immutable security audit log.
Every security event is appended to an append-only JSONL file and
echoed to stdout. The file is never overwritten — only appended.
"""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from app.config import get_settings
from app.models import SecurityEvent


class AuditLogger:
    """
    Append-only audit log writer.
    Thread-safe. Writes one JSON line per security event.
    The file is opened in append mode on every write to survive log rotation.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._path = self._settings.audit_log_path
        self._lock = Lock()
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: SecurityEvent) -> None:
        """
        Append a validated SecurityEvent to the audit log.
        Never raises — audit logging must not break the request pipeline.
        """
        data = event.model_dump(mode="json")
        line = json.dumps(data, default=str) + "\n"
        with self._lock:
            try:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(line)
            except OSError:
                # Fallback: at minimum print to stderr
                import sys
                print(f"[AUDIT FALLBACK] {line}", file=sys.stderr)

    def recent(self, limit: int = 50) -> list[dict]:
        """Return the most recent N events (newest last)."""
        try:
            lines = self._path.read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except (OSError, json.JSONDecodeError):
            return []


# Module-level singleton
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
