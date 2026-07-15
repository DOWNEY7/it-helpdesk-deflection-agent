"""
FastAPI middleware that auto-instruments every HTTP request.
Records latency, status code, and endpoint for all routes.
"""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics import http_request_duration_seconds, http_requests_total


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that wraps every request and emits:
      - http_request_duration_seconds (histogram)
      - http_requests_total (counter)
    Labels: method, endpoint (path template), status_code.
    """

    # Paths to skip (Prometheus scraper, health pings)
    _SKIP_PATHS = frozenset({"/metrics", "/favicon.ico"})

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500  # fallback if exception before response

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            labels = {
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": str(status_code),
            }
            http_request_duration_seconds.labels(**labels).observe(duration)
            http_requests_total.labels(**labels).inc()
