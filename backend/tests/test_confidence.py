"""
Tests for the confidence scoring and gate logic.
"""
from __future__ import annotations

import pytest

from app.models import Source
from app.services.confidence import ConfidenceGate, compute_confidence


def _make_source(relevance: float, article: str = "password-reset.md") -> Source:
    return Source(
        article=article,
        title="Password Reset Guide",
        section="Steps",
        relevance_score=relevance,
        chunk_id="abc123",
    )


class TestComputeConfidence:

    def test_no_sources_returns_zero(self):
        score = compute_confidence("how do I reset my password?", [])
        assert score == 0.0

    def test_high_relevance_single_source(self):
        sources = [_make_source(0.95)]
        score = compute_confidence("how do I reset my password?", sources)
        assert score > 0.5

    def test_multiple_high_sources_boosts_score(self):
        one_source = compute_confidence("password reset", [_make_source(0.8)])
        five_sources = compute_confidence(
            "password reset",
            [_make_source(0.8, f"article-{i}.md") for i in range(5)],
        )
        assert five_sources >= one_source

    def test_score_capped_at_one(self):
        sources = [_make_source(1.0, f"a{i}.md") for i in range(10)]
        score = compute_confidence("anything", sources)
        assert score <= 1.0

    def test_score_non_negative(self):
        score = compute_confidence("", [_make_source(0.0)])
        assert score >= 0.0

    def test_query_coverage_increases_score(self):
        """Query tokens that appear in article metadata should boost score."""
        sources = [Source(
            article="password-reset.md",
            title="Password Reset Guide",
            section="Password Reset Steps",
            relevance_score=0.5,
            chunk_id="x1",
        )]
        # Query with matching tokens
        score_match = compute_confidence("password reset guide", sources)
        # Query with no matching tokens
        score_no_match = compute_confidence("printer driver installation", sources)
        assert score_match > score_no_match


class TestConfidenceGate:

    def setup_method(self):
        self.gate = ConfidenceGate()

    def test_below_threshold_should_escalate(self):
        assert self.gate.should_escalate(0.60) is True
        assert self.gate.should_escalate(0.0) is True
        assert self.gate.should_escalate(0.69) is True

    def test_at_threshold_should_not_escalate(self):
        assert self.gate.should_escalate(0.70) is False

    def test_above_threshold_should_not_escalate(self):
        assert self.gate.should_escalate(0.80) is False
        assert self.gate.should_escalate(1.0) is False

    def test_low_confidence_range_needs_disclaimer(self):
        # 0.70 <= x < 0.85
        assert self.gate.needs_disclaimer(0.70) is True
        assert self.gate.needs_disclaimer(0.80) is True
        assert self.gate.needs_disclaimer(0.84) is True

    def test_high_confidence_no_disclaimer(self):
        assert self.gate.needs_disclaimer(0.85) is False
        assert self.gate.needs_disclaimer(1.0) is False

    def test_below_threshold_no_disclaimer(self):
        # Below threshold — escalated, not answered with disclaimer
        assert self.gate.needs_disclaimer(0.50) is False
