"""
KB article chunker.
Splits markdown articles into overlapping chunks for embedding and retrieval.
Used by the ingest script; also used in mock mode to serve chunks locally.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chunk:
    chunk_id: str
    article: str          # filename, e.g. "password-reset.md"
    title: str            # H1 title extracted from the article
    section: str          # Nearest H2/H3 heading above this chunk
    content: str          # Chunk text (cleaned markdown)
    char_count: int = field(init=False)
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.content)
        self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()


class KBChunker:
    """
    Splits a markdown article into chunks of ~500 chars with 100-char overlap.
    Preserves section headings as metadata.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk_file(self, path: Path) -> list[Chunk]:
        text = path.read_text(encoding="utf-8")
        return self.chunk_text(text, article=path.name)

    def chunk_text(self, text: str, article: str) -> list[Chunk]:
        # Extract H1 title
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else article.replace("-", " ").replace(".md", "").title()

        # Split into sections by headings
        sections = re.split(r"(^#{1,3}\s+.+$)", text, flags=re.MULTILINE)

        chunks: list[Chunk] = []
        current_section = "Overview"
        current_text = ""

        for part in sections:
            heading_match = re.match(r"^(#{1,3})\s+(.+)$", part.strip())
            if heading_match:
                # Flush current buffer
                if current_text.strip():
                    chunks.extend(
                        self._split_into_chunks(current_text, article, title, current_section)
                    )
                current_section = heading_match.group(2).strip()
                current_text = ""
            else:
                current_text += part

        # Flush final buffer
        if current_text.strip():
            chunks.extend(
                self._split_into_chunks(current_text, article, title, current_section)
            )

        return chunks

    def _split_into_chunks(
        self, text: str, article: str, title: str, section: str
    ) -> list[Chunk]:
        cleaned = self._clean_markdown(text)
        if not cleaned.strip():
            return []

        chunks = []
        start = 0
        idx = 0
        while start < len(cleaned):
            end = start + self._chunk_size
            chunk_text = cleaned[start:end].strip()
            if chunk_text:
                chunk_id = hashlib.sha256(
                    f"{article}:{section}:{idx}:{chunk_text[:50]}".encode()
                ).hexdigest()[:16]
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    article=article,
                    title=title,
                    section=section,
                    content=chunk_text,
                ))
                idx += 1
            start += self._chunk_size - self._overlap

        return chunks

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Remove markdown syntax leaving clean prose."""
        # Remove code fences
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Remove inline code
        text = re.sub(r"`[^`]+`", lambda m: m.group(0).strip("`"), text)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Remove image/link syntax but keep text
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Remove bold/italic markers
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
        text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def chunk_all_articles(kb_path: Path) -> list[Chunk]:
    """Chunk every .md file under kb_path."""
    chunker = KBChunker()
    all_chunks: list[Chunk] = []
    for md_file in sorted(kb_path.glob("*.md")):
        all_chunks.extend(chunker.chunk_file(md_file))
    return all_chunks
