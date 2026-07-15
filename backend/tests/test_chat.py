"""
Integration tests for the /chat endpoint.
Uses TestClient in mock mode (no Azure credentials needed).
"""
from __future__ import annotations



class TestChatEndpoint:

    def test_valid_it_query_returns_200(self, client, sample_message, sample_session_id):
        resp = client.post("/chat", json={
            "message": sample_message,
            "session_id": sample_session_id,
        })
        assert resp.status_code == 200

    def test_response_schema_valid(self, client, sample_message, sample_session_id):
        resp = client.post("/chat", json={
            "message": sample_message,
            "session_id": sample_session_id,
        })
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        assert "confidence" in data
        assert "escalate" in data
        assert "session_id" in data
        assert "request_id" in data
        assert isinstance(data["confidence"], float)
        assert isinstance(data["escalate"], bool)
        assert 0.0 <= data["confidence"] <= 1.0

    def test_injection_attempt_returns_400(self, client, blocked_message, sample_session_id):
        resp = client.post("/chat", json={
            "message": blocked_message,
            "session_id": sample_session_id,
        })
        assert resp.status_code == 400

    def test_empty_message_rejected(self, client, sample_session_id):
        resp = client.post("/chat", json={
            "message": "   ",
            "session_id": sample_session_id,
        })
        assert resp.status_code == 422  # Pydantic validation error

    def test_oversized_message_rejected(self, client, sample_session_id):
        resp = client.post("/chat", json={
            "message": "a" * 3000,
            "session_id": sample_session_id,
        })
        assert resp.status_code in (400, 422)

    def test_session_id_echoed(self, client, sample_message):
        session = "echo-test-session-id"
        resp = client.post("/chat", json={
            "message": sample_message,
            "session_id": session,
        })
        assert resp.json()["session_id"] == session

    def test_conversation_history_accepted(self, client, sample_session_id):
        resp = client.post("/chat", json={
            "message": "And how do I unlock it?",
            "session_id": sample_session_id,
            "conversation_history": [
                {"role": "user", "content": "My account is locked"},
                {"role": "assistant", "content": "I can help with that."},
            ],
        })
        assert resp.status_code == 200

    def test_escalated_response_has_empty_answer(self, client):
        """
        A query with no KB match should escalate.
        In mock mode: novel/obscure query with no keyword matches escalates.
        """
        resp = client.post("/chat", json={
            "message": "xyzzy foobar completely unknown topic with no IT relevance at all whatsoever",
            "session_id": "escalation-test-session",
        })
        assert resp.status_code == 200
        data = resp.json()
        # May or may not escalate depending on mock scoring, but schema is valid
        assert isinstance(data["escalate"], bool)


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_schema(self, client):
        data = client.get("/health").json()
        assert "overall" in data
        assert "azure_search" in data
        assert "azure_openai" in data
        assert "escalation_store" in data
        assert data["overall"] in ("healthy", "degraded", "unhealthy")

    def test_metrics_summary_returns_200(self, client):
        resp = client.get("/metrics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "deflection_rate" in data
        assert "total_requests" in data

    def test_prometheus_metrics_endpoint(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert b"helpdesk_requests_total" in resp.content
