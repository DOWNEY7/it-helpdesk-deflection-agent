"""
Confidence scoring service.
Computes a composite confidence score from retrieval signals.
Determines whether the agent should answer or escalate.
"""
from __future__ import annotations

from app.config import get_settings
from app.models import Source
from app.monitoring.metrics import rag_confidence_score


def _retrieval_score(sources: list[Source]) -> float:
    """
    Retrieval quality sub-score (0.0 – 1.0).
    Based on the top source's relevance and how many sources were found.
    """
    if not sources:
        return 0.0

    top_score = sources[0].relevance_score

    # Bonus for multiple corroborating sources (up to 3)
    coverage_bonus = min(len(sources) - 1, 2) * 0.05

    return min(top_score + coverage_bonus, 1.0)


def _query_coverage_score(query: str, sources: list[Source]) -> float:
    """
    Measures how many query tokens appear across retrieved chunks.
    Acts as a semantic relevance proxy without a second embedding call.
    """
    if not sources:
        return 0.0

    query_tokens = set(query.lower().split())
    if not query_tokens:
        return 0.0

    combined_text = " ".join(s.article + " " + s.section + " " + s.title for s in sources).lower()
    matched = sum(1 for t in query_tokens if t in combined_text)
    return matched / len(query_tokens)


def compute_confidence(query: str, sources: list[Source]) -> float:
    """
    Weighted composite confidence score:
      40% — retrieval relevance (top source score + coverage bonus)
      40% — query token coverage across retrieved metadata
      20% — source count bonus (more sources = more confidence)

    Returns a float in [0.0, 1.0].
    Also records the score in the Prometheus histogram.
    """
    if not sources:
        score = 0.0
        rag_confidence_score.observe(score)
        return score

    ret_score = _retrieval_score(sources)
    coverage = _query_coverage_score(query, sources)
    count_bonus = min(len(sources) / 5.0, 1.0) * 0.2

    score = (ret_score * 0.4) + (coverage * 0.4) + count_bonus
    score = round(min(score, 1.0), 4)

    rag_confidence_score.observe(score)
    return score


class ConfidenceGate:
    """
    Evaluates the confidence score and returns routing decision.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._threshold = settings.confidence_threshold
        self._low_threshold = settings.low_confidence_threshold

    def should_escalate(self, confidence: float) -> bool:
        return confidence < self._threshold

    def needs_disclaimer(self, confidence: float) -> bool:
        return self._threshold <= confidence < self._low_threshold


# Module-level singleton
_confidence_gate: ConfidenceGate | None = None


def get_confidence_gate() -> ConfidenceGate:
    global _confidence_gate
    if _confidence_gate is None:
        _confidence_gate = ConfidenceGate()
    return _confidence_gate
