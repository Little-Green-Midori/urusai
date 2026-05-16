"""Gemini Embedding 2 wrapper.

Model: gemini-embedding-2 (GA April 22, 2026).
- Multimodal: text / image / audio / video / PDF in a single embedding space.
- Default 3072-dim output; MRL allows truncation to 768 / 1536 / 3072 via
  `output_dimensionality`. Truncated vectors are auto-renormalised (unit norm).
- Per-call limits: 8192 text tokens, 6 images, 180s audio, 120s video,
  6-page PDF.

URUSAI uses 768 dim by default to balance Milvus storage and retrieval
quality. Multiple Gemini API keys can be supplied; the embedder rotates
through them via TokenRotator, retrying on 429 / quota errors.
"""
from __future__ import annotations

from typing import Any, Sequence

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from urusai.providers.base import Lane
from urusai.providers.rotation import NoAvailableTokenError, TokenRotator


_MIME_BY_MODALITY: dict[str, str] = {
    "image": "image/png",
    "audio": "audio/wav",
    "video": "video/mp4",
    "document": "application/pdf",
}


def _to_part(content: Any, modality: str) -> Any:
    """Wrap a single input into a Gemini-compatible content object."""
    if modality == "text":
        if not isinstance(content, str):
            raise TypeError(
                f"modality='text' requires str, got {type(content).__name__}"
            )
        return content
    if modality in _MIME_BY_MODALITY:
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError(
                f"modality={modality!r} requires bytes, got {type(content).__name__}"
            )
        return types.Part.from_bytes(
            data=bytes(content),
            mime_type=_MIME_BY_MODALITY[modality],
        )
    raise ValueError(f"unsupported modality: {modality!r}")


def _is_rate_limit(exc: Exception) -> bool:
    """Detect 429 / quota exhaustion from google-genai exceptions."""
    code = getattr(exc, "code", None)
    if code == 429:
        return True
    msg = str(exc).lower()
    return any(
        marker in msg
        for marker in ("429", "quota", "rate limit", "resource_exhausted")
    )


class GeminiEmbedder:
    """Wraps google-genai client.aio.models.embed_content for URUSAI usage."""

    lane: Lane = "api"
    modalities: frozenset[str] = frozenset(
        {"text", "image", "audio", "video", "document"}
    )

    def __init__(
        self,
        api_keys: list[str],
        output_dim: int = 768,
        model: str = "gemini-embedding-2",
    ):
        if not api_keys:
            raise ValueError("GeminiEmbedder requires at least one API key")
        self._rotator = TokenRotator(tokens=list(api_keys))
        self.output_dim = output_dim
        self.model = model
        self.name = f"google:{model}@{output_dim}"

    async def embed(self, content: Any, modality: str = "text") -> list[float]:
        """Embed a single piece of content. Returns a vector of length output_dim."""
        return (await self._embed_many([content], modality))[0]

    async def embed_batch(
        self,
        contents: Sequence[Any],
        modality: str = "text",
    ) -> list[list[float]]:
        """Embed a batch. Single API call for text; per-item calls for multimodal.

        gemini-embedding-2 aggregates all parts in one call into a single
        embedding (not one-per-part), so multimodal batches dispatch one
        call per item to keep a 1:1 mapping with the input list.
        """
        if not contents:
            return []
        if modality == "text":
            return await self._embed_many(list(contents), modality)
        results: list[list[float]] = []
        for item in contents:
            results.append((await self._embed_many([item], modality))[0])
        return results

    async def _embed_many(
        self,
        contents: list[Any],
        modality: str,
    ) -> list[list[float]]:
        wrapped = [_to_part(c, modality) for c in contents]
        last_exc: Exception | None = None
        for _ in range(len(self._rotator.tokens)):
            try:
                token = self._rotator.acquire()
            except NoAvailableTokenError as exc:
                last_exc = exc
                break
            client = genai.Client(api_key=token)
            try:
                response = await client.aio.models.embed_content(
                    model=self.model,
                    contents=wrapped,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.output_dim,
                    ),
                )
            except (ClientError, ServerError) as exc:
                last_exc = exc
                if _is_rate_limit(exc):
                    self._rotator.mark_rate_limited(token)
                    continue
                raise
            self._rotator.update_quota(token, remaining=999_999)
            values = [list(e.values) for e in (response.embeddings or [])]
            if len(values) != len(wrapped):
                raise RuntimeError(
                    f"gemini-embedding-2 returned {len(values)} embeddings "
                    f"for {len(wrapped)} inputs"
                )
            for i, vec in enumerate(values):
                if len(vec) != self.output_dim:
                    raise RuntimeError(
                        f"embedding {i} has {len(vec)} dims, expected {self.output_dim}"
                    )
            return values
        raise NoAvailableTokenError(
            f"all {len(self._rotator.tokens)} tokens exhausted; "
            f"last error: {last_exc!r}"
        )
