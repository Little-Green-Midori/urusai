"""Evidence claim writer — synchronise Postgres + Milvus.

For each EvidenceClaim batch:
1. INSERT into evidence_claims (Postgres, source-of-truth for structured fields).
2. Embed claim_text via the supplied embedder -> text_dense.
3. Insert vector row into the per-ingest Milvus collection. text_sparse is
   auto-populated by the BM25 Function defined on the collection schema.
   visual_dense is filled with a zero vector for channels without keyframe
   association; channels that carry visual context (ocr / vlm / scene)
   overwrite this in a later pass once visual frames are embedded.

The caller owns transaction lifecycle (commit / rollback on the AsyncSession)
and is responsible for opening the Milvus collection (`ensure_video_collection`
is called here, but the caller may pre-create with custom partition policy).
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from urusai.db.models import EvidenceClaim as EvidenceClaimRow
from urusai.db.retrieval import _domain_to_row_kwargs
from urusai.domain.evidence import EvidenceClaim
from urusai.rag.index.schema import ensure_video_collection


class _EmbedderLike(Protocol):
    """Minimal contract for the embedder dependency."""

    output_dim: int

    async def embed_batch(
        self, contents, modality: str = "text"
    ) -> list[list[float]]: ...


async def write_claims(
    claims: Iterable[EvidenceClaim],
    *,
    ingest_id: str,
    embedder: _EmbedderLike,
    session: AsyncSession,
    milvus_client: Any,
) -> int:
    """Persist a batch of claims to Postgres + Milvus. Returns the count written.

    Steps:
    1. Ensure the per-ingest Milvus collection exists.
    2. Convert each domain claim to a Postgres row (UUID id pre-assigned).
    3. Flush to Postgres so the rows are durable; an embedder failure cannot
       leave Milvus carrying vectors that no Postgres row references.
    4. Batch-embed the claim_text strings into 768-dim vectors.
    5. Insert one Milvus row per claim with text_dense set and visual_dense
       zeroed; the BM25 Function populates text_sparse on the Milvus side.
    """
    claim_list = list(claims)
    if not claim_list:
        return 0

    collection_name = ensure_video_collection(milvus_client, ingest_id)

    row_kwargs = [_domain_to_row_kwargs(c, ingest_id) for c in claim_list]
    pg_rows = [EvidenceClaimRow(**kw) for kw in row_kwargs]
    session.add_all(pg_rows)
    await session.flush()

    texts = [c.claim_text for c in claim_list]
    text_vectors = await embedder.embed_batch(texts, "text")
    if len(text_vectors) != len(claim_list):
        raise RuntimeError(
            f"embedder returned {len(text_vectors)} vectors for "
            f"{len(claim_list)} claims"
        )

    zero_visual = [0.0] * embedder.output_dim
    milvus_rows = [
        {
            "evidence_id": row.id,
            "channel": row.channel,
            "start_sec": row.start_sec,
            "end_sec": row.end_sec,
            "claim_text": row.claim_text,
            "text_dense": vec,
            "visual_dense": zero_visual,
        }
        for row, vec in zip(pg_rows, text_vectors)
    ]
    milvus_client.insert(collection_name=collection_name, data=milvus_rows)

    return len(claim_list)
