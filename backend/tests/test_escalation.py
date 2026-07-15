"""
Tests for escalation ticket creation and persistence.
"""
from __future__ import annotations

import pytest

from app.models import Message
from app.services.escalation import EscalationService, _classify_category, _classify_urgency


@pytest.fixture
def service():
    return EscalationService()


@pytest.fixture
def sample_history():
    return [
        Message(role="user", content="My account is locked and I can't log in."),
        Message(role="assistant", content="I'll help you with that."),
        Message(role="user", content="It's urgent — I have a deadline."),
    ]


class TestCategoryClassification:

    @pytest.mark.parametrize("text,expected", [
        ("I can't reset my password", "access"),
        ("VPN won't connect to corporate network", "network"),
        ("Teams is not showing my meetings in Outlook", "m365"),
        ("The office printer is not mapping correctly", "hardware"),
        ("Adobe Acrobat won't install from Software Centre", "software"),
        ("I received a phishing email with a suspicious link", "security"),
        ("My shared mailbox is not showing in Outlook", "email"),
    ])
    def test_category_classification(self, text, expected):
        result = _classify_category(text)
        assert result == expected, f"Expected {expected}, got {result} for: {text!r}"


class TestUrgencyClassification:

    @pytest.mark.parametrize("text,expected", [
        ("Complete system outage — all users are down", "critical"),
        ("Urgent: I cannot access my account at all", "high"),
        ("Teams is sometimes slow during calls", "medium"),
        ("How do I configure out of office in Outlook?", "low"),
    ])
    def test_urgency_classification(self, text, expected):
        result = _classify_urgency(text)
        assert result == expected


class TestTicketCreation:

    def test_ticket_has_valid_id(self, service, sample_history):
        ticket = service.create_ticket(
            conversation_history=sample_history,
            confidence_score=0.3,
            session_id="test-session",
        )
        assert ticket.ticket_id.startswith("TKT-")
        assert len(ticket.ticket_id) > 10

    def test_ticket_category_assigned(self, service, sample_history):
        ticket = service.create_ticket(
            conversation_history=sample_history,
            confidence_score=0.3,
            session_id="test-session",
        )
        assert ticket.category in (
            "access", "network", "m365", "hardware", "software", "security", "email", "other"
        )

    def test_ticket_urgency_assigned(self, service, sample_history):
        ticket = service.create_ticket(
            conversation_history=sample_history,
            confidence_score=0.3,
            session_id="test-session",
        )
        assert ticket.urgency in ("low", "medium", "high", "critical")

    def test_ticket_status_is_open(self, service, sample_history):
        ticket = service.create_ticket(
            conversation_history=sample_history,
            confidence_score=0.3,
            session_id="test-session",
        )
        assert ticket.status == "open"

    def test_ticket_summary_not_empty(self, service, sample_history):
        ticket = service.create_ticket(
            conversation_history=sample_history,
            confidence_score=0.3,
            session_id="test-session",
        )
        assert len(ticket.summary) > 5

    def test_retrieval_miss_flag(self, service, sample_history):
        ticket = service.create_ticket(
            conversation_history=sample_history,
            confidence_score=0.1,
            session_id="test-session",
            retrieval_miss=True,
        )
        assert ticket.retrieval_miss is True


class TestEscalationEndpoints:

    def test_list_tickets_returns_200(self, client):
        resp = client.get("/escalations")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_tickets_with_status_filter(self, client):
        resp = client.get("/escalations?status=open")
        assert resp.status_code == 200

    def test_get_nonexistent_ticket_returns_404(self, client):
        resp = client.get("/escalations/TKT-DOESNOTEXIST")
        assert resp.status_code == 404

    def test_update_nonexistent_ticket_returns_404(self, client):
        resp = client.patch(
            "/escalations/TKT-DOESNOTEXIST",
            json={"status": "in_progress"},
        )
        assert resp.status_code == 404
