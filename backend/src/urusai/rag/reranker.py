"""Optional reranker hook — BGE-reranker-v2-m3 / Voyage / Zerank.

Optional reranker hook over hybrid search hits. Not a strict release requirement
(reranker hook only); enable when single-pass hybrid retrieval underperforms.
"""
from __future__ import annotations

from typing import Protocol


class Reranker(Protocol):
    """Reorder a candidate list by query relevance."""

    name: str

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 10,
    ) -> list[dict]: ...
