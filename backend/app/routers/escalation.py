"""
Escalation queue router — for the IT team admin dashboard.
GET  /escalations        — list tickets (with optional filters)
GET  /escalations/{id}   — get single ticket
PATCH /escalations/{id}  — update status / assign / resolve
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.models import (
    EscalationTicket,
    TicketCategory,
    TicketStatus,
    TicketUpdateRequest,
)
from app.services.escalation import get_escalation_service

router = APIRouter(prefix="/escalations", tags=["escalations"])


@router.get("", response_model=list[EscalationTicket])
async def list_escalations(
    ticket_status: TicketStatus | None = Query(default=None, alias="status"),
    category: TicketCategory | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EscalationTicket]:
    """Return escalation tickets, newest first. Optionally filter by status/category."""
    return get_escalation_service().list_tickets(
        status=ticket_status, category=category, limit=limit
    )


@router.get("/{ticket_id}", response_model=EscalationTicket)
async def get_escalation(ticket_id: str) -> EscalationTicket:
    """Return a single ticket by ID."""
    ticket = get_escalation_service().get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found.",
        )
    return ticket


@router.patch("/{ticket_id}", response_model=EscalationTicket)
async def update_escalation(
    ticket_id: str, body: TicketUpdateRequest
) -> EscalationTicket:
    """Update ticket status, assignee, or resolution notes."""
    ticket = get_escalation_service().update_ticket(ticket_id, body)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found.",
        )
    return ticket
