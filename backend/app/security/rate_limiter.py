"""
Security rate limiter — sliding-window per-session and per-IP.
Implemented in-memory (swap for Redis in production for multi-instance deployments).
"""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque
from threading import Lock

from app.config import get_settings


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter.
    Tracks request timestamps in a deque per key and evicts stale entries.
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Returns (allowed, requests_remaining).
        Thread-safe; evicts expired timestamps before checking.
        """
        now = time.time()
        cutoff = now - self._window

        with self._lock:
            dq = self._windows[key]
            # Remove timestamps outside the window
            while dq and dq[0] < cutoff:
                dq.popleft()

            if len(dq) >= self._max:
                return False, 0

            dq.append(now)
            return True, self._max - len(dq)

    def reset(self, key: str) -> None:
        """Clear the window for a key (used in tests)."""
        with self._lock:
            self._windows.pop(key, None)


class RateLimiterService:
    """
    Composite rate limiter enforcing both per-session and per-IP limits.
    Uses SHA-256 to hash IPs before storing (privacy-preserving).
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._session_limiter = SlidingWindowRateLimiter(
            max_requests=settings.rate_limit_per_session,
            window_seconds=settings.rate_limit_window_seconds,
        )
        self._ip_limiter = SlidingWindowRateLimiter(
            max_requests=settings.rate_limit_per_ip,
            window_seconds=settings.rate_limit_ip_window_seconds,
        )

    @staticmethod
    def hash_ip(ip: str) -> str:
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def check(self, session_id: str, client_ip: str) -> tuple[bool, str]:
        """
        Returns (allowed, scope_that_was_exceeded).
        scope: "" if allowed, "session" or "ip" if blocked.
        """
        allowed_session, _ = self._session_limiter.is_allowed(session_id)
        if not allowed_session:
            return False, "session"

        ip_hash = self.hash_ip(client_ip)
        allowed_ip, _ = self._ip_limiter.is_allowed(ip_hash)
        if not allowed_ip:
            return False, "ip"

        return True, ""

    def reset_session(self, session_id: str) -> None:
        self._session_limiter.reset(session_id)


# Module-level singleton
_rate_limiter: RateLimiterService | None = None


def get_rate_limiter() -> RateLimiterService:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiterService()
    return _rate_limiter
