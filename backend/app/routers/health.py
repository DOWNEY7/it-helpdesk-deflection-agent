"""
Health and metrics routers.
GET /health         — deep health check (all dependencies)
GET /metrics        — Prometheus text exposition
GET /metrics/summary — JSON business KPI snapshot
GET /security/events — recent security audit log entries
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.models import HealthStatus, MetricsSummary
from app.monitoring.health_checks import run_health_checks
from app.monitoring.metrics import REGISTRY
from app.security.audit_log import get_audit_logger

router = APIRouter(tags=["observability"])

_start_time = time.time()


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    """Deep health check for all downstream dependencies."""
    return await run_health_checks()


@router.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    """Prometheus text format — scraped by Prometheus every 15s."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@router.get("/metrics/summary", response_model=MetricsSummary)
async def metrics_summary() -> MetricsSummary:
    """
    High-level JSON business KPI snapshot.
    Pulled by monitor.html every 30 seconds for the in-app dashboard.
    """
    from app.routers.chat import _total_deflections, _total_requests

    total = _total_requests
    deflected = _total_deflections
    escalated = total - deflected

    deflection_rate = round(deflected / total, 4) if total > 0 else 0.0

    # Pull recent security events count from audit log
    recent_events = get_audit_logger().recent(limit=200)
    blocks_today = sum(
        1 for e in recent_events
        if e.get("action_taken") == "blocked"
    )

    return MetricsSummary(
        deflection_rate=deflection_rate,
        total_requests=total,
        total_deflections=deflected,
        total_escalations=max(escalated, 0),
        security_blocks_today=blocks_today,
    )


@router.get("/security/events")
async def security_events(limit: int = 50) -> list[dict]:
    """Return the most recent security audit log entries (newest last)."""
    return get_audit_logger().recent(limit=limit)


@router.get("/uptime")
async def uptime() -> dict:
    """Returns seconds since application start."""
    uptime_secs = round(time.time() - _start_time, 1)
    return {"uptime_seconds": uptime_secs}
