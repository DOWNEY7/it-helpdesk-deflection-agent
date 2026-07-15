"""
All Pydantic data models / schemas for the application.
Every API request and response is validated through these models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Primitives
# ─────────────────────────────────────────────────────────────────────────────

class Source(BaseModel):
    """A retrieved KB article chunk that was used to answer the query."""
    article: str = Field(..., description="KB article filename, e.g. password-reset.md")
    title: str = Field(..., description="Human-readable article title")
    section: str = Field(default="", description="Section heading within article")
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    chunk_id: str = Field(..., description="Unique chunk identifier for traceability")


class Message(BaseModel):
    """A single turn in a conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# Chat Request / Response
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Inbound chat message from the employee."""
    message: Annotated[str, Field(min_length=1, max_length=2000)]
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_history: list[Message] = Field(default_factory=list, max_length=10)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be blank or whitespace only.")
        return v.strip()


class ChatResponse(BaseModel):
    """Outbound response — either an answer or an escalation signal."""
    answer: str = Field(default="", description="Agent's answer (empty if escalated)")
    sources: list[Source] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    escalate: bool = Field(..., description="True if confidence below threshold")
    session_id: str
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    low_confidence_disclaimer: bool = Field(
        default=False,
        description="True when 0.70 ≤ confidence < 0.85",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Escalation Ticket
# ─────────────────────────────────────────────────────────────────────────────

TicketCategory = Literal[
    "access", "network", "m365", "hardware", "software", "security", "email", "other"
]
TicketUrgency = Literal["low", "medium", "high", "critical"]
TicketStatus  = Literal["open", "in_progress", "resolved", "closed"]


class EscalationTicket(BaseModel):
    """Structured ticket created when the agent cannot confidently answer."""
    ticket_id: str = Field(default_factory=lambda: f"TKT-{datetime.utcnow():%Y%m%d}-{str(uuid4())[:8].upper()}")
    summary: str = Field(..., description="1-2 sentence summary of the issue")
    category: TicketCategory
    urgency: TicketUrgency
    conversation_history: list[Message]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    retrieval_miss: bool = Field(
        default=False,
        description="True if no KB chunks were retrieved",
    )
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: TicketStatus = Field(default="open")
    assigned_to: str | None = Field(default=None)
    resolved_at: datetime | None = Field(default=None)
    resolution_notes: str | None = Field(default=None)


class TicketUpdateRequest(BaseModel):
    """Payload for IT team to update a ticket status."""
    status: TicketStatus
    assigned_to: str | None = None
    resolution_notes: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Security Events
# ─────────────────────────────────────────────────────────────────────────────

ThreatType = Literal[
    "prompt_injection",
    "prompt_poisoning",
    "prompt_flooding",
    "jailbreak",
    "context_manipulation",
    "pii_in_output",
    "xss_attempt",
    "oversized_input",
    "invalid_session",
    "rate_limit_exceeded",
]

SecurityAction  = Literal["blocked", "warned", "logged"]
SecuritySeverity = Literal["low", "medium", "high", "critical"]


class SecurityEvent(BaseModel):
    """A security-relevant event detected by the guardrail pipeline."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    ip_hash: str = Field(default="unknown", description="SHA-256 of client IP")
    threat_type: ThreatType
    severity: SecuritySeverity
    action_taken: SecurityAction
    rule_triggered: str = Field(default="")
    input_snippet: str = Field(
        default="",
        max_length=100,
        description="First 100 chars of input only",
    )


class GuardResult(BaseModel):
    """Result of passing input through the security guardrail pipeline."""
    allowed: bool
    threat_type: ThreatType | None = None
    severity: SecuritySeverity | None = None
    rule_triggered: str = ""
    sanitised_input: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Health & Metrics
# ─────────────────────────────────────────────────────────────────────────────

ServiceStatus = Literal["healthy", "degraded", "unhealthy"]


class HealthStatus(BaseModel):
    """Deep health check result covering all downstream dependencies."""
    overall: ServiceStatus
    azure_search: ServiceStatus
    azure_openai: ServiceStatus
    escalation_store: ServiceStatus
    latency_ms: dict[str, float] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")


class MetricsSummary(BaseModel):
    """High-level business metrics snapshot (returned by /metrics/summary)."""
    deflection_rate: float = Field(..., ge=0.0, le=1.0)
    total_requests: int = Field(..., ge=0)
    total_deflections: int = Field(..., ge=0)
    total_escalations: int = Field(..., ge=0)
    security_blocks_today: int = Field(default=0)
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(default=0.0)
    period: str = Field(default="last_1h")
