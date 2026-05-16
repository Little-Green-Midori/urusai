"""Unit tests for GeminiEmbedder — mocked google-genai client; no API calls."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai.errors import ClientError

from urusai.providers.rotation import NoAvailableTokenError
from urusai.rag.embedder import GeminiEmbedder, _is_rate_limit, _to_part


# === helpers ===


def _mock_response(num_vectors: int, dim: int = 768):
    response = MagicMock()
    response.embeddings = [
        MagicMock(values=[0.0] * dim) for _ in range(num_vectors)
    ]
    return response


def _fake_rate_limit_error(message: str = "429 Quota exceeded: RESOURCE_EXHAUSTED"):
    """Build a ClientError instance without calling its constructor.

    google-genai's ClientError requires specific construction args; bypass that
    so the exception type-check (`isinstance(..., ClientError)`) still passes.
    """
    err = ClientError.__new__(ClientError)
    Exception.__init__(err, message)
    err.code = 429
    return err


def _patch_client(responses_or_errors: list) -> patch:
    """Patch `urusai.rag.embedder.genai.Client` so each call pops one item.

    Items are returned in order. Exceptions are raised; everything else is
    returned from `embed_content`.
    """
    state = {"i": 0}

    async def embed_content(**_):
        i = state["i"]
        state["i"] = i + 1
        item = responses_or_errors[i]
        if isinstance(item, Exception):
            raise item
        return item

    def make_client(*_, **__):
        client = MagicMock()
        client.aio.models.embed_content = AsyncMock(side_effect=embed_content)
        return client

    return patch("urusai.rag.embedder.genai.Client", side_effect=make_client)


# === construction + helpers ===


def test_init_rejects_empty_keys():
    with pytest.raises(ValueError, match="at least one API key"):
        GeminiEmbedder(api_keys=[])


def test_init_records_name_dim_model():
    em = GeminiEmbedder(api_keys=["k"], output_dim=1536, model="gemini-embedding-2")
    assert em.output_dim == 1536
    assert em.model == "gemini-embedding-2"
    assert em.name == "google:gemini-embedding-2@1536"
    assert em.lane == "api"


def test_to_part_text_passthrough():
    assert _to_part("hello", "text") == "hello"


def test_to_part_text_requires_str():
    with pytest.raises(TypeError, match="text"):
        _to_part(b"raw", "text")


def test_to_part_image_requires_bytes():
    with pytest.raises(TypeError, match="image"):
        _to_part("not bytes", "image")


def test_to_part_image_wraps_bytes():
    part = _to_part(b"\x89PNG\r\n", "image")
    assert part is not None  # types.Part instance


def test_to_part_unsupported_modality():
    with pytest.raises(ValueError, match="unsupported modality"):
        _to_part("anything", "fish")


def test_is_rate_limit_detects_429_code():
    class FakeExc(Exception):
        def __init__(self, msg, code=None):
            super().__init__(msg)
            self.code = code

    assert _is_rate_limit(FakeExc("over quota", code=429))
    assert _is_rate_limit(FakeExc("Rate limit hit"))
    assert _is_rate_limit(FakeExc("429 Too Many Requests"))
    assert _is_rate_limit(FakeExc("RESOURCE_EXHAUSTED"))
    assert not _is_rate_limit(FakeExc("Invalid argument", code=400))
    assert not _is_rate_limit(FakeExc("unknown failure"))


# === async happy paths ===


async def test_embed_single_text_happy_path():
    em = GeminiEmbedder(api_keys=["k1"], output_dim=768)
    with _patch_client([_mock_response(1, dim=768)]):
        vec = await em.embed("hello world", "text")
    assert isinstance(vec, list)
    assert len(vec) == 768


async def test_embed_batch_text_single_call():
    em = GeminiEmbedder(api_keys=["k1"], output_dim=768)
    with _patch_client([_mock_response(3, dim=768)]):
        vectors = await em.embed_batch(["a", "b", "c"], "text")
    assert len(vectors) == 3
    assert all(len(v) == 768 for v in vectors)


async def test_embed_batch_empty_short_circuits():
    em = GeminiEmbedder(api_keys=["k1"], output_dim=768)
    with patch("urusai.rag.embedder.genai.Client") as patched:
        result = await em.embed_batch([], "text")
    assert result == []
    patched.assert_not_called()


# === rate-limit rotation + exhaustion ===


async def test_embed_rotates_token_on_rate_limit():
    em = GeminiEmbedder(api_keys=["k1", "k2"], output_dim=768)
    with _patch_client([_fake_rate_limit_error(), _mock_response(1, dim=768)]):
        vec = await em.embed("hello", "text")
    assert len(vec) == 768


async def test_embed_raises_when_all_tokens_exhausted():
    em = GeminiEmbedder(api_keys=["k1", "k2"], output_dim=768)
    with _patch_client([_fake_rate_limit_error(), _fake_rate_limit_error()]):
        with pytest.raises(NoAvailableTokenError):
            await em.embed("hello", "text")


async def test_embed_validates_returned_dim():
    em = GeminiEmbedder(api_keys=["k1"], output_dim=768)
    with _patch_client([_mock_response(1, dim=512)]):  # wrong dim
        with pytest.raises(RuntimeError, match="dims, expected 768"):
            await em.embed("hello", "text")


async def test_embed_validates_returned_count():
    em = GeminiEmbedder(api_keys=["k1"], output_dim=768)
    with _patch_client([_mock_response(2, dim=768)]):  # 2 embeddings for 1 input
        with pytest.raises(RuntimeError, match="returned 2 embeddings for 1 inputs"):
            await em.embed("hello", "text")
