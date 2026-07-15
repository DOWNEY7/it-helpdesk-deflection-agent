"""
KB ingestion script.
Reads all markdown articles from /kb, chunks them, computes embeddings,
and uploads to Azure AI Search. Run once, or on KB updates.

Usage:
    python scripts/ingest_kb.py [--kb-path ../kb] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Safety: reject articles with embedded instruction patterns
_POISON_PATTERNS = [
    re.compile(r"(?i)\bIGNORE\s+(ALL\s+)?PREVIOUS\s+INSTRUCTIONS?\b"),
    re.compile(r"(?i)\bACT\s+AS\b"),
    re.compile(r"(?i)\bSYSTEM\s+PROMPT\b"),
    re.compile(r"(?i)\bDISREGARD\b"),
    re.compile(r"(?i)<\s*/?(?:system|instructions?)\s*>"),
]


def _check_article_safety(path: Path, content: str) -> bool:
    """Return True if the article is safe to ingest."""
    for pattern in _POISON_PATTERNS:
        if pattern.search(content):
            print(f"  [SKIP] {path.name} — poisoning pattern detected: {pattern.pattern!r}")
            return False
    return True


def _compute_article_checksum(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def ingest(kb_path: Path, dry_run: bool = False) -> None:
    print(f"Ingesting KB from: {kb_path.resolve()}")

    # Import chunker
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.utils.chunker import KBChunker

    chunker = KBChunker()
    articles = sorted(kb_path.glob("*.md"))
    print(f"Found {len(articles)} articles.")

    all_documents = []
    checksums = {}

    for article_path in articles:
        content = article_path.read_text(encoding="utf-8")
        print(f"  Processing: {article_path.name} ({len(content)} chars)")

        # Safety check
        if not _check_article_safety(article_path, content):
            continue

        checksum = _compute_article_checksum(content)
        checksums[article_path.name] = checksum

        chunks = chunker.chunk_file(article_path)
        print(f"    → {len(chunks)} chunks created")

        for chunk in chunks:
            doc = {
                "chunk_id": chunk.chunk_id,
                "article": chunk.article,
                "title": chunk.title,
                "section": chunk.section,
                "content": chunk.content,
                "content_hash": chunk.content_hash,
                "article_checksum": checksum,
            }
            all_documents.append(doc)

    print(f"\nTotal documents to index: {len(all_documents)}")

    # Save checksums manifest
    manifest_path = kb_path.parent / "data" / "kb_checksums.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(checksums, indent=2))
    print(f"Checksum manifest saved: {manifest_path}")

    if dry_run:
        print("\n[DRY RUN] No documents uploaded to Azure AI Search.")
        return

    # Upload to Azure AI Search
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        from app.config import get_settings

        settings = get_settings()
        if not settings.azure_configured:
            print("\n[WARN] Azure not configured — skipping upload. Use --dry-run for local testing.")
            return

        client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=AzureKeyCredential(settings.azure_search_api_key),
        )

        # Upload in batches of 100
        batch_size = 100
        for i in range(0, len(all_documents), batch_size):
            batch = all_documents[i : i + batch_size]
            result = client.upload_documents(documents=batch)
            succeeded = sum(1 for r in result if r.succeeded)
            print(f"  Batch {i//batch_size + 1}: {succeeded}/{len(batch)} uploaded successfully")

        print(f"\nIngestion complete. {len(all_documents)} chunks indexed.")

    except ImportError:
        print("\n[ERROR] azure-search-documents not installed. Run: pip install azure-search-documents")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Ingestion failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest KB articles into Azure AI Search")
    parser.add_argument("--kb-path", default="../kb", help="Path to KB directory")
    parser.add_argument("--dry-run", action="store_true", help="Parse and chunk only, do not upload")
    args = parser.parse_args()

    kb_path = Path(args.kb_path)
    if not kb_path.exists():
        print(f"[ERROR] KB path not found: {kb_path.resolve()}")
        sys.exit(1)

    ingest(kb_path, dry_run=args.dry_run)
