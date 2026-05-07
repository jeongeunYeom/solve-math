from __future__ import annotations

import json
from pathlib import Path

from math_tutor_agent.models import TextbookChunk, to_plain_dict


class TextbookStore:
    """In-memory store for licensed textbook chunks.

    This MVP keeps chunks in process so the storage layer can later be replaced by
    PostgreSQL + pgvector without changing the tutor orchestration API.
    """

    def __init__(self, chunks: list[TextbookChunk] | None = None) -> None:
        self._chunks: list[TextbookChunk] = chunks or []

    @classmethod
    def from_json(cls, path: str | Path) -> TextbookStore:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("chunks", [])
        return cls([TextbookChunk.from_dict(item) for item in raw])

    def to_json(self, path: str | Path) -> None:
        payload = [to_plain_dict(chunk) for chunk in self._chunks]
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, chunk: TextbookChunk) -> None:
        self._chunks.append(chunk)

    def extend(self, chunks: list[TextbookChunk]) -> None:
        self._chunks.extend(chunks)

    def all(self) -> list[TextbookChunk]:
        return list(self._chunks)

    def filter(
        self,
        *,
        publisher: str | None = None,
        grade: str | None = None,
        subject: str | None = None,
    ) -> list[TextbookChunk]:
        chunks = self._chunks
        if publisher:
            chunks = [chunk for chunk in chunks if chunk.publisher == publisher]
        if grade:
            chunks = [chunk for chunk in chunks if chunk.grade == grade]
        if subject:
            chunks = [chunk for chunk in chunks if chunk.subject == subject]
        return list(chunks)
