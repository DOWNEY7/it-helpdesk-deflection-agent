"""
Structured log event schemas — every log line is a typed Pydantic model.
No freetext logging. Every field is validated before write.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class BaseLogEvent(BaseModel):
    """Base fields present on every log event."""
    event: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel = "INFO"
    environment: str = "development"
    request_id: str = Field(default_factory=lambda: str(uuid4()))


class RequestLogEvent(BaseLogEvent):
    """Emitted once per chat request, capturing the full pipeline trace."""
    event: str = "chat_request"
    session_id: str
    user_query_length: int
    retrieval_chunks: int
    retrieval_latency_ms: float
    confidence_score: float
    escalated: bool
    llm_latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    sources_cited: list[str] = Field(default_factory=list)
    low_confidence_disclaimer: bool = False
    mock_mode: bool = False


class SecurityLogEvent(BaseLogEvent):
    """Emitted every time the security pipeline blocks or flags a request."""
    event: str = "security_block"
    level: LogLevel = "WARNING"
    session_id: str
    ip_hash: str = "unknown"
    threat_type: str
    severity: str
    action_taken: str
    rule_triggered: str = ""
    input_snippet: str = ""  # max 100 chars


class EscalationLogEvent(BaseLogEvent):
    """Emitted when an escalation ticket is created."""
    event: str = "escalation_created"
    ticket_id: str
    category: str
    urgency: str
    confidence_score: float
    conversation_turns: int
    retrieval_miss: bool


class HealthCheckLogEvent(BaseLogEvent):
    """Emitted by the background health probe every 60 seconds."""
    event: str = "health_check"
    azure_search: str
    azure_openai: str
    escalation_store: str
    overall: str
    latency_ms: dict[str, float] = Field(default_factory=dict)


class IngestLogEvent(BaseLogEvent):
    """Emitted during KB ingestion."""
    event: str = "kb_ingest"
    article: str
    chunks_created: int
    chunk_hashes: list[str] = Field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


class ErrorLogEvent(BaseLogEvent):
    """Emitted when an unhandled error occurs."""
    event: str = "error"
    level: LogLevel = "ERROR"
    error_type: str
    error_message: str
    traceback_snippet: str = ""
    session_id: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)
