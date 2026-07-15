"""
Escalation ticket service.
Creates, stores, retrieves, and updates escalation tickets.
Storage: local JSON file (drop-in swap for CosmosDB).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from threading import Lock

from app.models import (
    EscalationTicket,
    Message,
    TicketCategory,
    TicketStatus,
    TicketUpdateRequest,
)
from app.monitoring.metrics import helpdesk_escalations_total

_STORE_PATH = Path("./data/escalations.json")
_LOCK = Lock()

# ─────────────────────────────────────────────────────────────────────────────
# Category + urgency classification helpers
# ─────────────────────────────────────────────────────────────────────────────

_CATEGORY_SIGNALS: dict[str, list[str]] = {
    "access": ["password", "login", "account", "mfa", "sso", "lockout", "credential", "permission", "access", "provision", "leaver"],
    "network": ["vpn", "wifi", "network", "internet", "proxy", "firewall", "connection", "cisco", "globalprotect"],
    "m365": ["teams", "outlook", "onedrive", "sharepoint", "office", "365", "microsoft", "licence", "license", "subscription"],
    "hardware": ["laptop", "computer", "monitor", "dock", "usb", "keyboard", "mouse", "screen", "bios", "device"],
    "software": ["install", "software", "app", "application", "chrome", "edge", "browser", "java", "adobe", "update"],
    "security": ["phishing", "virus", "malware", "bitlocker", "encryption", "suspicious", "threat", "ransomware"],
    "email": ["email", "mail", "inbox", "outlook", "mailbox", "distribution", "spam", "out of office"],
}

_URGENCY_SIGNALS: dict[str, list[str]] = {
    "critical": ["down", "outage", "breach", "ransomware", "cannot work", "all users", "everyone", "production"],
    "high": ["urgent", "asap", "immediately", "blocking", "cannot access", "broken", "not working"],
    "medium": ["slow", "intermittent", "sometimes", "occasionally", "degraded"],
    "low": ["question", "query", "when", "how do i", "where", "information"],
}


def _classify_category(text: str) -> TicketCategory:
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for cat, signals in _CATEGORY_SIGNALS.items():
        scores[cat] = sum(1 for s in signals if s in text_lower)
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "other"  # type: ignore[return-value]


def _classify_urgency(text: str) -> str:
    text_lower = text.lower()
    for urgency in ("critical", "high", "medium", "low"):
        signals = _URGENCY_SIGNALS[urgency]
        if any(s in text_lower for s in signals):
            return urgency
    return "medium"


def _summarise_conversation(history: list[Message]) -> str:
    """Build a 1-2 sentence summary from conversation turns."""
    user_turns = [m.content for m in history if m.role == "user"]
    if not user_turns:
        return "Employee raised an IT support request."
    first = user_turns[0][:200]
    if len(user_turns) > 1:
        last = user_turns[-1][:100]
        return f"Employee asked: '{first}'. Follow-up: '{last}'."
    return f"Employee asked: '{first}'."


# ─────────────────────────────────────────────────────────────────────────────
# Storage helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_store() -> list[dict]:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _STORE_PATH.exists():
        return []
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_store(tickets: list[dict]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(tickets, default=str, indent=2), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

class EscalationService:

    def create_ticket(
        self,
        conversation_history: list[Message],
        confidence_score: float,
        session_id: str,
        retrieval_miss: bool = False,
    ) -> EscalationTicket:
        """Create and persist a new escalation ticket."""
        full_text = " ".join(m.content for m in conversation_history)
        category = _classify_category(full_text)
        urgency = _classify_urgency(full_text)
        summary = _summarise_conversation(conversation_history)

        ticket = EscalationTicket(
            summary=summary,
            category=category,          # type: ignore[arg-type]
            urgency=urgency,            # type: ignore[arg-type]
            conversation_history=conversation_history,
            confidence_score=confidence_score,
            session_id=session_id,
            retrieval_miss=retrieval_miss,
        )

        helpdesk_escalations_total.labels(
            category=category, urgency=urgency
        ).inc()

        with _LOCK:
            tickets = _load_store()
            tickets.append(ticket.model_dump(mode="json"))
            _save_store(tickets)

        return ticket

    def list_tickets(
        self,
        status: TicketStatus | None = None,
        category: TicketCategory | None = None,
        limit: int = 50,
    ) -> list[EscalationTicket]:
        with _LOCK:
            raw = _load_store()

        tickets = [EscalationTicket.model_validate(t) for t in raw]

        if status:
            tickets = [t for t in tickets if t.status == status]
        if category:
            tickets = [t for t in tickets if t.category == category]

        tickets.sort(key=lambda t: t.created_at, reverse=True)
        return tickets[:limit]

    def get_ticket(self, ticket_id: str) -> EscalationTicket | None:
        with _LOCK:
            raw = _load_store()
        for item in raw:
            if item.get("ticket_id") == ticket_id:
                return EscalationTicket.model_validate(item)
        return None

    def update_ticket(
        self, ticket_id: str, update: TicketUpdateRequest
    ) -> EscalationTicket | None:
        with _LOCK:
            tickets = _load_store()
            for item in tickets:
                if item.get("ticket_id") == ticket_id:
                    item["status"] = update.status
                    if update.assigned_to is not None:
                        item["assigned_to"] = update.assigned_to
                    if update.resolution_notes is not None:
                        item["resolution_notes"] = update.resolution_notes
                    if update.status == "resolved":
                        item["resolved_at"] = datetime.utcnow().isoformat()
                    _save_store(tickets)
                    return EscalationTicket.model_validate(item)
        return None


# Module-level singleton
_escalation_service: EscalationService | None = None


def get_escalation_service() -> EscalationService:
    global _escalation_service
    if _escalation_service is None:
        _escalation_service = EscalationService()
    return _escalation_service
