from __future__ import annotations

import re
from collections import Counter

from math_tutor_agent.models import RetrievedChunk, TextbookChunk
from math_tutor_agent.store import TextbookStore

TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


class KeywordRetriever:
    """Simple lexical retriever for textbook chunks."""

    def __init__(self, store: TextbookStore, top_k: int = 3) -> None:
        self.store = store
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        *,
        publisher: str | None = None,
        grade: str | None = "고1",
        subject: str | None = None,
    ) -> list[RetrievedChunk]:
        query_tokens = Counter(_tokenize(query))
        results: list[RetrievedChunk] = []
        for chunk in self.store.filter(publisher=publisher, grade=grade, subject=subject):
            score, matched = self._score(query_tokens, chunk)
            if score > 0:
                results.append(RetrievedChunk(chunk=chunk, score=score, matched_keywords=matched))
        return sorted(results, key=lambda item: item.score, reverse=True)[: self.top_k]

    def _score(self, query_tokens: Counter[str], chunk: TextbookChunk) -> tuple[float, list[str]]:
        keyword_tokens = {_normalize(keyword) for keyword in chunk.keywords + [chunk.concept]}
        content_tokens = set(_tokenize(chunk.content))
        matched_keywords = sorted(
            token for token in keyword_tokens if token and token in query_tokens
        )
        token_overlap = query_tokens.keys() & content_tokens
        score = (2.0 * len(matched_keywords)) + (0.5 * len(token_overlap))
        return score, matched_keywords


def _tokenize(text: str) -> list[str]:
    return [_normalize(token) for token in TOKEN_RE.findall(text)]


def _normalize(token: str) -> str:
    return token.casefold().strip()
