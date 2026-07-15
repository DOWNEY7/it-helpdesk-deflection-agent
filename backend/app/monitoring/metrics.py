"""
Prometheus metrics registry — all 25 application metrics defined here.
Import `METRICS` or individual collectors in any service that needs to emit.
"""
from __future__ import annotations

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
)

# ── Shared registry (avoids duplicate registration in tests) ──────────────────
REGISTRY = CollectorRegistry(auto_describe=True)

# ─────────────────────────────────────────────────────────────────────────────
# Business KPIs
# ─────────────────────────────────────────────────────────────────────────────

helpdesk_requests_total = Counter(
    "helpdesk_requests_total",
    "Every incoming chat request",
    ["outcome"],          # "deflected" | "escalated" | "blocked" | "error"
    registry=REGISTRY,
)

helpdesk_deflections_total = Counter(
    "helpdesk_deflections_total",
    "Requests answered without escalation",
    registry=REGISTRY,
)

helpdesk_escalations_total = Counter(
    "helpdesk_escalations_total",
    "Requests that triggered an escalation ticket",
    ["category", "urgency"],
    registry=REGISTRY,
)

helpdesk_deflection_rate = Gauge(
    "helpdesk_deflection_rate",
    "Rolling deflection rate (updated on each request)",
    registry=REGISTRY,
)

helpdesk_active_sessions = Gauge(
    "helpdesk_user_sessions_active",
    "Sessions that have sent a message in the last 15 minutes",
    registry=REGISTRY,
)

# ─────────────────────────────────────────────────────────────────────────────
# RAG Quality
# ─────────────────────────────────────────────────────────────────────────────

rag_retrieval_hits_total = Counter(
    "rag_retrieval_hits_total",
    "Retrievals that returned at least one chunk",
    registry=REGISTRY,
)

rag_retrieval_misses_total = Counter(
    "rag_retrieval_misses_total",
    "Retrievals returning zero results",
    registry=REGISTRY,
)

rag_confidence_score = Histogram(
    "rag_confidence_score",
    "Distribution of confidence scores",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0],
    registry=REGISTRY,
)

rag_chunks_retrieved = Histogram(
    "rag_chunks_retrieved",
    "Number of chunks returned per query",
    buckets=[0, 1, 2, 3, 4, 5],
    registry=REGISTRY,
)

rag_retrieval_latency_seconds = Histogram(
    "rag_retrieval_latency_seconds",
    "Azure AI Search round-trip time in seconds",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=REGISTRY,
)

# ─────────────────────────────────────────────────────────────────────────────
# LLM Performance
# ─────────────────────────────────────────────────────────────────────────────

llm_request_latency_seconds = Histogram(
    "llm_request_latency_seconds",
    "End-to-end GPT-4o-mini response time",
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 15.0],
    registry=REGISTRY,
)

llm_prompt_tokens_total = Counter(
    "llm_prompt_tokens_total",
    "Total prompt tokens consumed",
    registry=REGISTRY,
)

llm_completion_tokens_total = Counter(
    "llm_completion_tokens_total",
    "Total completion tokens generated",
    registry=REGISTRY,
)

llm_errors_total = Counter(
    "llm_errors_total",
    "LLM API failures",
    ["error_type"],   # "timeout" | "rate_limit" | "server_error" | "unknown"
    registry=REGISTRY,
)

llm_token_cost_usd = Counter(
    "llm_token_cost_usd_total",
    "Estimated accumulated cost in USD (gpt-4o-mini pricing)",
    registry=REGISTRY,
)

# ─────────────────────────────────────────────────────────────────────────────
# Security Events
# ─────────────────────────────────────────────────────────────────────────────

security_blocked_requests_total = Counter(
    "security_blocked_requests_total",
    "Requests blocked by any guardrail layer",
    ["threat_type"],
    registry=REGISTRY,
)

security_rate_limit_hits_total = Counter(
    "security_rate_limit_hits_total",
    "HTTP 429s issued",
    ["scope"],   # "session" | "ip"
    registry=REGISTRY,
)

security_injection_detections_total = Counter(
    "security_injection_detections_total",
    "Prompt injection pattern matches detected",
    ["pattern_id"],
    registry=REGISTRY,
)

security_pii_detections_total = Counter(
    "security_pii_detections_total",
    "PII entities found in LLM output",
    ["entity_type"],
    registry=REGISTRY,
)

security_jailbreak_attempts_total = Counter(
    "security_jailbreak_attempts_total",
    "OOD / jailbreak classifier triggers",
    registry=REGISTRY,
)

# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure
# ─────────────────────────────────────────────────────────────────────────────

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Per-endpoint HTTP request latency",
    ["method", "endpoint", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 3.0, 8.0, 15.0],
    registry=REGISTRY,
)

http_requests_total = Counter(
    "http_requests_total",
    "All requests by method and status code",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

app_uptime_seconds = Gauge(
    "app_uptime_seconds",
    "Seconds since last application start",
    registry=REGISTRY,
)

service_health_status = Gauge(
    "service_health_status",
    "Dependency health: 1 = healthy, 0 = unhealthy",
    ["service"],   # "azure_search" | "azure_openai" | "escalation_store"
    registry=REGISTRY,
)

app_info = Info(
    "helpdesk_app",
    "Application build information",
    registry=REGISTRY,
)
app_info.info({"version": "1.0.0", "environment": "development"})


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

# gpt-4o-mini pricing (July 2025) — $0.15 / 1M prompt, $0.60 / 1M completion
_PROMPT_COST_PER_TOKEN  = 0.15 / 1_000_000
_COMPLETION_COST_PER_TOKEN = 0.60 / 1_000_000


def record_llm_usage(prompt_tokens: int, completion_tokens: int) -> None:
    """Record token counts and estimated cost in one call."""
    llm_prompt_tokens_total.inc(prompt_tokens)
    llm_completion_tokens_total.inc(completion_tokens)
    cost = (prompt_tokens * _PROMPT_COST_PER_TOKEN
            + completion_tokens * _COMPLETION_COST_PER_TOKEN)
    llm_token_cost_usd.inc(cost)


def update_deflection_rate(deflections: int, total: int) -> None:
    """Recalculate and update the deflection rate gauge."""
    if total > 0:
        helpdesk_deflection_rate.set(deflections / total)
