"""Gemini Embedding 2 wrapper.

gemini-embedding-2 wrapper; 768-dim MRL output for text + multimodal claims.

Model: gemini-embedding-2
- Multimodal: text / image / video (up to 120s) / audio / PDF (up to 6 pages)
- MRL dimensions: 128-3072, recommended 768 / 1536 / 3072
- Auto-renormalises truncated dimensions (768 -> unit-norm)
- 8192-token text input limit
"""
from __future__ import annotations

from typing import Any

from urusai.providers.base import EmbeddingProvider, Lane


class GeminiEmbedder:
    """Wraps google-genai client.models.embed_content for URUSAI usage."""

    name: str = "google:gemini-embedding-2@768"
    lane: Lane = "api"
    output_dim: int = 768
    modalities: frozenset[str] = frozenset({"text", "image", "audio", "video", "document"})

    def __init__(self, api_keys: list[str], output_dim: int = 768):
        self.api_keys = api_keys
        self.output_dim = output_dim

    async def embed(self, content: Any, modality: str) -> list[float]:
        """Embed text or media to fixed-dim vector via gemini-embedding-2."""
        # TODO: implement
        # 1) acquire token via TokenRotator
        # 2) call client.models.embed_content(model="gemini-embedding-2",
        #                                     contents=..., config=EmbedContentConfig(output_dimensionality=self.output_dim))
        # 3) rotator.update_quota(token, remaining=...) on success
        # 4) rotator.mark_rate_limited(token) on 429
        return [0.0] * self.output_dim
