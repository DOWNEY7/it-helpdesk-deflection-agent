"""
RAG retrieval service.
Wraps Azure AI Search with hybrid (keyword + vector) search.
Falls back to local keyword search in mock mode.
"""
from __future__ import annotations

import time
from pathlib import Path

from app.config import get_settings
from app.models import Source
from app.monitoring.metrics import (
    rag_chunks_retrieved,
    rag_retrieval_hits_total,
    rag_retrieval_latency_seconds,
    rag_retrieval_misses_total,
)
from app.utils.chunker import chunk_all_articles


class RetrievalService:
    """
    Retrieves relevant KB chunks for a given query.
    In real mode: Azure AI Search hybrid search.
    In mock mode: TF-IDF-style keyword overlap scoring over local files.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._mock_chunks = None  # lazy-loaded

    # ── Public API ─────────────────────────────────────────────────────────

    async def retrieve(self, query: str) -> list[Source]:
        """
        Return up to max_retrieval_chunks sources relevant to the query.
        Also updates Prometheus metrics.
        """
        start = time.perf_counter()

        if self._settings.mock_mode or not self._settings.azure_configured:
            results = self._mock_retrieve(query)
        else:
            results = await self._azure_retrieve(query)

        latency = time.perf_counter() - start
        rag_retrieval_latency_seconds.observe(latency)
        rag_chunks_retrieved.observe(len(results))

        if results:
            rag_retrieval_hits_total.inc()
        else:
            rag_retrieval_misses_total.inc()

        return results

    # ── Azure AI Search ────────────────────────────────────────────────────

    async def _azure_retrieve(self, query: str) -> list[Source]:
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents.aio import SearchClient
            from azure.search.documents.models import VectorizedQuery
        except ImportError:
            return self._mock_retrieve(query)

        s = self._settings
        async with SearchClient(
            endpoint=s.azure_search_endpoint,
            index_name=s.azure_search_index_name,
            credential=AzureKeyCredential(s.azure_search_api_key),
        ) as client:
            results = await client.search(
                search_text=query,
                top=s.max_retrieval_chunks,
                select=["chunk_id", "article", "title", "section", "content"],
                query_type="semantic",
                semantic_configuration_name="default",
            )

            sources = []
            async for r in results:
                score = r.get("@search.reranker_score") or r.get("@search.score") or 0.0
                sources.append(Source(
                    article=r["article"],
                    title=r["title"],
                    section=r.get("section", ""),
                    relevance_score=min(float(score) / 4.0, 1.0),  # normalise 0-4 → 0-1
                    chunk_id=r["chunk_id"],
                ))

            return sources

    # ── Mock retrieval (local keyword overlap) ─────────────────────────────

    def _mock_retrieve(self, query: str) -> list[Source]:
        if self._mock_chunks is None:
            kb_path = self._settings.kb_path
            if not kb_path.is_absolute():
                kb_path = (Path(__file__).parent.parent.parent.parent / kb_path).resolve()
            self._mock_chunks = chunk_all_articles(kb_path)

        query_tokens = set(query.lower().split())
        scored: list[tuple[float, object]] = []

        for chunk in self._mock_chunks:
            chunk_tokens = set(chunk.content.lower().split())
            overlap = len(query_tokens & chunk_tokens)
            if overlap > 0:
                score = overlap / max(len(query_tokens), 1)
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: self._settings.max_retrieval_chunks]

        return [
            Source(
                article=chunk.article,
                title=chunk.title,
                section=chunk.section,
                relevance_score=round(min(score, 1.0), 3),
                chunk_id=chunk.chunk_id,
            )
            for score, chunk in top
        ]

    def get_chunk_text(self, source: Source) -> str:
        """
        Return the raw text for a source chunk (used to build the LLM prompt).
        In mock mode: reads from local chunks.
        """
        if self._mock_chunks is None:
            self._mock_retrieve("")  # trigger load

        for chunk in (self._mock_chunks or []):
            if chunk.chunk_id == source.chunk_id:
                return chunk.content
        return ""


# Module-level singleton
_retrieval_service: RetrievalService | None = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
