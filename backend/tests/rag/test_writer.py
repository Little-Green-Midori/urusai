"""Unit tests for write_claims + ensure_video_collection — fully mocked."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from urusai.domain.evidence import (
    ConfidenceMarker,
    EvidenceClaim,
    TimeRange,
)
from urusai.rag.index.schema import (
    collection_name_for,
    ensure_video_collection,
)
from urusai.rag.writer import write_claims


# === fixtures ===


def _claim(text: str, start: float, end: float, channel: str = "dialogue") -> EvidenceClaim:
    return EvidenceClaim(
        channel=channel,
        time_range=TimeRange(start=start, end=end),
        claim_text=text,
        raw_quote=text,
        confidence=ConfidenceMarker.CLEAR,
        source_tool="manual_subs_en",
    )


def _fake_embedder(output_dim: int = 768, vectors_per_call: int | None = None):
    """Build a mock embedder whose embed_batch returns `vectors_per_call` zeros."""
    em = MagicMock()
    em.output_dim = output_dim

    async def embed_batch(contents, modality="text"):
        n = vectors_per_call if vectors_per_call is not None else len(list(contents))
        return [[0.1] * output_dim for _ in range(n)]

    em.embed_batch = AsyncMock(side_effect=embed_batch)
    return em


def _fake_session():
    session = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    return session


def _fake_milvus_client(has_collection: bool = True):
    client = MagicMock()
    client.has_collection = MagicMock(return_value=has_collection)
    client.create_collection = MagicMock()
    client.insert = MagicMock()
    index_params = MagicMock()
    index_params.add_index = MagicMock()
    client.prepare_index_params = MagicMock(return_value=index_params)
    return client


# === ensure_video_collection ===


def test_ensure_collection_idempotent_when_exists():
    client = _fake_milvus_client(has_collection=True)
    name = ensure_video_collection(client, "abc123")
    assert name == "urusai_v_abc123"
    client.has_collection.assert_called_once_with(collection_name="urusai_v_abc123")
    client.create_collection.assert_not_called()


def test_ensure_collection_creates_when_missing():
    client = _fake_milvus_client(has_collection=False)
    client.create_schema = MagicMock(return_value=MagicMock())
    name = ensure_video_collection(client, "abc123")
    assert name == "urusai_v_abc123"
    client.create_collection.assert_called_once()
    call_kwargs = client.create_collection.call_args.kwargs
    assert call_kwargs["collection_name"] == "urusai_v_abc123"
    assert client.prepare_index_params.return_value.add_index.call_count == 3


def test_collection_name_for():
    assert collection_name_for("xyz") == "urusai_v_xyz"


# === write_claims ===


async def test_write_claims_empty_returns_zero():
    em = _fake_embedder()
    session = _fake_session()
    client = _fake_milvus_client()
    n = await write_claims(
        [], ingest_id="i1", embedder=em, session=session, milvus_client=client
    )
    assert n == 0
    em.embed_batch.assert_not_called()
    client.insert.assert_not_called()
    session.add_all.assert_not_called()


async def test_write_claims_writes_to_pg_and_milvus():
    em = _fake_embedder(output_dim=768)
    session = _fake_session()
    client = _fake_milvus_client(has_collection=True)
    claims = [
        _claim("hello world", 0.0, 2.0),
        _claim("goodbye world", 2.0, 4.0),
    ]
    n = await write_claims(
        claims,
        ingest_id="i1",
        embedder=em,
        session=session,
        milvus_client=client,
    )
    assert n == 2
    session.add_all.assert_called_once()
    pg_rows = session.add_all.call_args.args[0]
    assert len(pg_rows) == 2
    session.flush.assert_awaited_once()
    em.embed_batch.assert_awaited_once()
    embed_args = em.embed_batch.await_args
    assert list(embed_args.args[0]) == ["hello world", "goodbye world"]
    assert embed_args.args[1] == "text"
    client.insert.assert_called_once()
    insert_kwargs = client.insert.call_args.kwargs
    assert insert_kwargs["collection_name"] == "urusai_v_i1"
    rows = insert_kwargs["data"]
    assert len(rows) == 2
    for row in rows:
        assert set(row.keys()) == {
            "evidence_id",
            "channel",
            "start_sec",
            "end_sec",
            "claim_text",
            "text_dense",
            "visual_dense",
        }
        assert len(row["text_dense"]) == 768
        assert row["visual_dense"] == [0.0] * 768
    assert rows[0]["claim_text"] == "hello world"
    assert rows[1]["claim_text"] == "goodbye world"


async def test_write_claims_creates_collection_when_missing():
    em = _fake_embedder(output_dim=768)
    session = _fake_session()
    client = _fake_milvus_client(has_collection=False)
    client.create_schema = MagicMock(return_value=MagicMock())
    await write_claims(
        [_claim("x", 0.0, 1.0)],
        ingest_id="new_ingest",
        embedder=em,
        session=session,
        milvus_client=client,
    )
    client.create_collection.assert_called_once()
    assert (
        client.create_collection.call_args.kwargs["collection_name"]
        == "urusai_v_new_ingest"
    )


async def test_write_claims_raises_when_embedder_returns_wrong_count():
    em = _fake_embedder(output_dim=768, vectors_per_call=1)
    session = _fake_session()
    client = _fake_milvus_client(has_collection=True)
    claims = [_claim("a", 0.0, 1.0), _claim("b", 1.0, 2.0)]
    with pytest.raises(RuntimeError, match="returned 1 vectors for 2 claims"):
        await write_claims(
            claims,
            ingest_id="i1",
            embedder=em,
            session=session,
            milvus_client=client,
        )
    client.insert.assert_not_called()


async def test_write_claims_zero_visual_dim_matches_embedder():
    em = _fake_embedder(output_dim=1536)
    session = _fake_session()
    client = _fake_milvus_client(has_collection=True)
    await write_claims(
        [_claim("hi", 0.0, 0.5)],
        ingest_id="i1",
        embedder=em,
        session=session,
        milvus_client=client,
    )
    rows = client.insert.call_args.kwargs["data"]
    assert len(rows[0]["visual_dense"]) == 1536
