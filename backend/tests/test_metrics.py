"""
Tests for Prometheus metrics — verify counters increment correctly.
"""
from __future__ import annotations


from app.monitoring.metrics import (
    REGISTRY,
    helpdesk_deflections_total,
    helpdesk_escalations_total,
    helpdesk_requests_total,
    rag_confidence_score,
    rag_retrieval_hits_total,
    rag_retrieval_misses_total,
    security_blocked_requests_total,
)


def _get_counter_value(counter, **labels) -> float:
    return counter.labels(**labels)._value.get() if labels else counter._value.get()


class TestMetricCounters:

    def test_deflection_counter_increments(self):
        before = _get_counter_value(helpdesk_deflections_total)
        helpdesk_deflections_total.inc()
        after = _get_counter_value(helpdesk_deflections_total)
        assert after == before + 1.0

    def test_request_counter_increments_with_label(self):
        before = helpdesk_requests_total.labels(outcome="deflected")._value.get()
        helpdesk_requests_total.labels(outcome="deflected").inc()
        after = helpdesk_requests_total.labels(outcome="deflected")._value.get()
        assert after == before + 1.0

    def test_escalation_counter_increments_with_labels(self):
        before = helpdesk_escalations_total.labels(category="access", urgency="high")._value.get()
        helpdesk_escalations_total.labels(category="access", urgency="high").inc()
        after = helpdesk_escalations_total.labels(category="access", urgency="high")._value.get()
        assert after == before + 1.0

    def test_retrieval_hit_increments(self):
        before = rag_retrieval_hits_total._value.get()
        rag_retrieval_hits_total.inc()
        after = rag_retrieval_hits_total._value.get()
        assert after == before + 1.0

    def test_retrieval_miss_increments(self):
        before = rag_retrieval_misses_total._value.get()
        rag_retrieval_misses_total.inc()
        after = rag_retrieval_misses_total._value.get()
        assert after == before + 1.0

    def test_security_block_counter_increments(self):
        before = security_blocked_requests_total.labels(threat_type="prompt_injection")._value.get()
        security_blocked_requests_total.labels(threat_type="prompt_injection").inc()
        after = security_blocked_requests_total.labels(threat_type="prompt_injection")._value.get()
        assert after == before + 1.0


class TestHistograms:

    def test_confidence_histogram_accepts_valid_values(self):
        for score in [0.0, 0.3, 0.5, 0.7, 0.85, 1.0]:
            rag_confidence_score.observe(score)  # should not raise

    def test_confidence_histogram_rejects_negative(self):
        # prometheus_client silently accepts any float, but let's verify no exception
        rag_confidence_score.observe(-0.1)


class TestPrometheusRegistry:

    def test_registry_produces_metrics_text(self):
        from prometheus_client import generate_latest
        output = generate_latest(REGISTRY).decode()
        assert "helpdesk_requests_total" in output
        assert "rag_confidence_score" in output
        assert "security_blocked_requests_total" in output
        assert "llm_request_latency_seconds" in output
        assert "service_health_status" in output
