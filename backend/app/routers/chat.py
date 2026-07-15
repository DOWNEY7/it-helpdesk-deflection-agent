"""
Chat router — the primary endpoint for employee IT support queries.
POST /chat
"""
from __future__ import annotations

import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models import (
    ChatRequest,
    ChatResponse,
    EscalationTicket,
    Message,
)
from app.monitoring.log_schema import ErrorLogEvent, RequestLogEvent
from app.security.input_guard import get_input_guard
from app.security.output_guard import get_output_guard
from app.services.confidence import compute_confidence, get_confidence_gate
from app.services.escalation import get_escalation_service
from app.services.generation import get_generation_service
from app.services.retrieval import get_retrieval_service
from app.monitoring.metrics import (
    helpdesk_deflections_total,
    helpdesk_requests_total,
    update_deflection_rate,
)
from app.utils.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])

# Rolling counters for deflection rate gauge
_total_requests = 0
_total_deflections = 0


@router.post(
    "",
    response_model=ChatResponse,
    responses={
        200: {"description": "Answer or escalation signal"},
        400: {"description": "Invalid or blocked input"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Upstream service unavailable"},
    },
)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    global _total_requests, _total_deflections

    request_id = str(uuid4())
    client_ip = request.client.host if request.client else "unknown"
    start = time.perf_counter()

    # ── Stage 1: Input guardrail ───────────────────────────────────────────
    guard = get_input_guard()
    guard_result = guard.validate(
        text=body.message,
        session_id=body.session_id,
        client_ip=client_ip,
    )

    if not guard_result.allowed:
        threat = guard_result.threat_type or "unknown"
        helpdesk_requests_total.labels(outcome="blocked").inc()
        if threat == "rate_limit_exceeded":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before sending another message.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your message was blocked by the security filter ({threat}). "
                   "Please rephrase your IT support question.",
        )

    sanitised_query = guard_result.sanitised_input

    # ── Stage 2: Retrieval ─────────────────────────────────────────────────
    retrieval_start = time.perf_counter()
    retrieval_svc = get_retrieval_service()
    sources = await retrieval_svc.retrieve(sanitised_query)
    retrieval_latency_ms = (time.perf_counter() - retrieval_start) * 1000

    # ── Stage 3: Confidence scoring ────────────────────────────────────────
    confidence = compute_confidence(sanitised_query, sources)
    gate = get_confidence_gate()
    should_escalate = gate.should_escalate(confidence)
    needs_disclaimer = gate.needs_disclaimer(confidence)

    # ── Stage 4a: Escalation path ──────────────────────────────────────────
    if should_escalate:
        history = list(body.conversation_history) + [
            Message(role="user", content=sanitised_query)
        ]
        ticket: EscalationTicket = get_escalation_service().create_ticket(
            conversation_history=history,
            confidence_score=confidence,
            session_id=body.session_id,
            retrieval_miss=(len(sources) == 0),
        )

        helpdesk_requests_total.labels(outcome="escalated").inc()
        _total_requests += 1
        update_deflection_rate(_total_deflections, _total_requests)

        logger.emit(RequestLogEvent(
            request_id=request_id,
            session_id=body.session_id,
            user_query_length=len(body.message),
            retrieval_chunks=len(sources),
            retrieval_latency_ms=round(retrieval_latency_ms, 1),
            confidence_score=confidence,
            escalated=True,
            llm_latency_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            sources_cited=[],
        ))

        return ChatResponse(
            answer="",
            sources=[],
            confidence=confidence,
            escalate=True,
            session_id=body.session_id,
            request_id=request_id,
        )

    # ── Stage 4b: Generation path ──────────────────────────────────────────
    chunk_texts = {
        src.chunk_id: retrieval_svc.get_chunk_text(src)
        for src in sources
    }

    llm_start = time.perf_counter()
    try:
        answer, prompt_tokens, completion_tokens = await get_generation_service().generate(
            query=sanitised_query,
            sources=sources,
            chunk_texts=chunk_texts,
            conversation_history=body.conversation_history,
        )
    except Exception as exc:
        helpdesk_requests_total.labels(outcome="error").inc()
        logger.emit(ErrorLogEvent(
            request_id=request_id,
            error_type=type(exc).__name__,
            error_message=str(exc)[:500],
            session_id=body.session_id,
        ))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable. Please try again shortly.",
        )

    llm_latency_ms = (time.perf_counter() - llm_start) * 1000

    # ── Stage 5: Output guardrail ──────────────────────────────────────────
    output_guard = get_output_guard()
    guard_out = output_guard.scan(answer)

    if not guard_out.safe:
        # PII found in LLM output — escalate rather than return unsafe content
        history = list(body.conversation_history) + [
            Message(role="user", content=sanitised_query)
        ]
        get_escalation_service().create_ticket(
            conversation_history=history,
            confidence_score=confidence,
            session_id=body.session_id,
        )
        helpdesk_requests_total.labels(outcome="escalated").inc()
        _total_requests += 1
        return ChatResponse(
            answer="",
            sources=[],
            confidence=0.0,
            escalate=True,
            session_id=body.session_id,
            request_id=request_id,
        )

    # ── Stage 6: Success response ──────────────────────────────────────────
    helpdesk_deflections_total.inc()
    helpdesk_requests_total.labels(outcome="deflected").inc()
    _total_requests += 1
    _total_deflections += 1
    update_deflection_rate(_total_deflections, _total_requests)

    logger.emit(RequestLogEvent(
        request_id=request_id,
        session_id=body.session_id,
        user_query_length=len(body.message),
        retrieval_chunks=len(sources),
        retrieval_latency_ms=round(retrieval_latency_ms, 1),
        confidence_score=confidence,
        escalated=False,
        llm_latency_ms=round(llm_latency_ms, 1),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        sources_cited=[s.article for s in sources],
        low_confidence_disclaimer=needs_disclaimer,
    ))

    return ChatResponse(
        answer=guard_out.sanitised,
        sources=sources,
        confidence=confidence,
        escalate=False,
        session_id=body.session_id,
        request_id=request_id,
        low_confidence_disclaimer=needs_disclaimer,
    )
