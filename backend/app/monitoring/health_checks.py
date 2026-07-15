"""
Deep health checks for all downstream dependencies.
Called by GET /health and the background probe every 60 seconds.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import httpx

from app.config import get_settings
from app.models import HealthStatus, ServiceStatus
from app.monitoring.metrics import service_health_status


async def _check_azure_search() -> tuple[ServiceStatus, float]:
    """Ping Azure AI Search with a minimal list-indexes request."""
    settings = get_settings()
    if settings.mock_mode or not settings.azure_search_endpoint:
        return "healthy", 0.0

    url = (
        f"{settings.azure_search_endpoint.rstrip('/')}"
        f"/indexes?api-version=2023-11-01&$select=name&$top=1"
    )
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                url, headers={"api-key": settings.azure_search_api_key}
            )
        latency = (time.perf_counter() - start) * 1000
        if resp.status_code == 200:
            return "healthy", latency
        return "degraded", latency
    except Exception:
        return "unhealthy", (time.perf_counter() - start) * 1000


async def _check_azure_openai() -> tuple[ServiceStatus, float]:
    """Ping Azure OpenAI models endpoint (lightweight, no token spend)."""
    settings = get_settings()
    if settings.mock_mode or not settings.azure_openai_endpoint:
        return "healthy", 0.0

    url = (
        f"{settings.azure_openai_endpoint.rstrip('/')}"
        f"/openai/models?api-version={settings.azure_openai_api_version}"
    )
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                url, headers={"api-key": settings.azure_openai_api_key}
            )
        latency = (time.perf_counter() - start) * 1000
        if resp.status_code in (200, 404):  # 404 is fine — endpoint is reachable
            return "healthy", latency
        return "degraded", latency
    except Exception:
        return "unhealthy", (time.perf_counter() - start) * 1000


async def _check_escalation_store() -> tuple[ServiceStatus, float]:
    """Check that the escalation store path is readable/writable."""

    start = time.perf_counter()
    store_path = Path("./data/escalations.json")
    try:
        store_path.parent.mkdir(parents=True, exist_ok=True)
        if not store_path.exists():
            store_path.write_text("[]")
        store_path.read_text()
        latency = (time.perf_counter() - start) * 1000
        return "healthy", latency
    except Exception:
        return "unhealthy", (time.perf_counter() - start) * 1000


async def run_health_checks() -> HealthStatus:
    """Run all dependency checks concurrently and return aggregated status."""
    search_result, openai_result, store_result = await asyncio.gather(
        _check_azure_search(),
        _check_azure_openai(),
        _check_escalation_store(),
    )

    # Unpack tuples
    s_status, s_lat = search_result
    o_status, o_lat = openai_result
    st_status, st_lat = store_result

    # Update Prometheus gauges
    service_health_status.labels(service="azure_search").set(
        1 if s_status == "healthy" else 0
    )
    service_health_status.labels(service="azure_openai").set(
        1 if o_status == "healthy" else 0
    )
    service_health_status.labels(service="escalation_store").set(
        1 if st_status == "healthy" else 0
    )

    # Overall is the worst status of any dependency
    statuses = [s_status, o_status, st_status]
    if "unhealthy" in statuses:
        overall: ServiceStatus = "unhealthy"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return HealthStatus(
        overall=overall,
        azure_search=s_status,
        azure_openai=o_status,
        escalation_store=st_status,
        latency_ms={
            "azure_search": round(s_lat, 1),
            "azure_openai": round(o_lat, 1),
            "escalation_store": round(st_lat, 1),
        },
    )
