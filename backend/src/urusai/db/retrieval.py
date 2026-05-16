"""DB-backed retrieval, ingest CRUD, and same-layer conflict detection.

Retrieval ranks SQL substring matches first, then confidence
(clear > blurry > inferred), then start_sec ascending. Vector ANN retrieval
through Milvus replaces the substring step in the RAG retriever layer;
confidence + time ordering remain as final tiebreakers.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from urusai.db.models import EvidenceClaim as EvidenceClaimRow
from urusai.db.models import Ingest as IngestRow
from urusai.db.models import QueryEvidenceLog, QueryLog
from urusai.domain.evidence import (
    ChannelSpec,
    ConfidenceMarker,
    EvidenceClaim,
    InferenceStrength,
    TimeRange,
)
from urusai.domain.inventory import InventoryReport


# === SQL helpers ===

_CONFIDENCE_RANK = case(
    {
        ConfidenceMarker.CLEAR.value: 3,
        ConfidenceMarker.BLURRY.value: 2,
        ConfidenceMarker.INFERRED.value: 1,
    },
    value=EvidenceClaimRow.confidence,
    else_=0,
)


def _row_to_domain(row: EvidenceClaimRow) -> EvidenceClaim:
    return EvidenceClaim(
        channel=row.channel,
        time_range=TimeRange(start=row.start_sec, end=row.end_sec),
        claim_text=row.claim_text,
        raw_quote=row.raw_quote,
        confidence=ConfidenceMarker(row.confidence),
        source_tool=row.source_tool,
        source_spec=(
            ChannelSpec(**row.source_spec) if row.source_spec else None
        ),
        inference_strength=(
            InferenceStrength(row.inference_strength)
            if row.inference_strength
            else None
        ),
        inference_chain=row.inference_chain,
    )


def _domain_to_row_kwargs(c: EvidenceClaim, ingest_id: str) -> dict[str, Any]:
    return dict(
        id=str(uuid.uuid4()),
        ingest_id=ingest_id,
        channel=c.channel,
        start_sec=c.time_range.start,
        end_sec=c.time_range.end,
        claim_text=c.claim_text,
        raw_quote=c.raw_quote,
        confidence=c.confidence.value,
        source_tool=c.source_tool,
        source_spec=(c.source_spec.model_dump() if c.source_spec else None),
        inference_strength=(
            c.inference_strength.value if c.inference_strength else None
        ),
        inference_chain=c.inference_chain,
        extra_metadata={},
    )


# === Ingest CRUD ===


async def create_ingest(
    session: AsyncSession,
    *,
    ingest_id: str,
    inventory: InventoryReport,
    url: str | None = None,
    status: str = "ready",
) -> IngestRow:
    row = IngestRow(
        id=ingest_id,
        source_path=inventory.source_path,
        url=url,
        video_id=inventory.video_id,
        inventory=inventory.model_dump(),
        status=status,
    )
    session.add(row)
    await session.flush()
    return row


async def get_ingest(session: AsyncSession, ingest_id: str) -> IngestRow | None:
    return await session.get(IngestRow, ingest_id)


async def list_ingests(session: AsyncSession) -> list[IngestRow]:
    stmt = select(IngestRow).order_by(IngestRow.created_at.desc())
    return list((await session.scalars(stmt)).all())


async def delete_ingest(session: AsyncSession, ingest_id: str) -> bool:
    row = await session.get(IngestRow, ingest_id)
    if row is None:
        return False
    await session.delete(row)
    await session.flush()
    return True


async def evidence_count_by_channel(
    session: AsyncSession, ingest_id: str
) -> dict[str, int]:
    stmt = (
        select(EvidenceClaimRow.channel, func.count(EvidenceClaimRow.id))
        .where(EvidenceClaimRow.ingest_id == ingest_id)
        .group_by(EvidenceClaimRow.channel)
    )
    result = await session.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


# === Evidence insertion ===


async def insert_evidence_batch(
    session: AsyncSession,
    ingest_id: str,
    claims: Iterable[EvidenceClaim],
) -> int:
    rows = [EvidenceClaimRow(**_domain_to_row_kwargs(c, ingest_id)) for c in claims]
    if not rows:
        return 0
    session.add_all(rows)
    await session.flush()
    return len(rows)


# === Retrieval ===


async def retrieve_evidence(
    session: AsyncSession,
    *,
    ingest_id: str,
    query: str,
    channels: list[str] | None = None,
    limit: int = 50,
) -> tuple[list[str], list[EvidenceClaim]]:
    """SQL substring rank + confidence-ordered retrieval.

    Substring matches rank highest; among ties, confidence rank
    (clear > blurry > inferred); then start_sec ascending. Vector ANN
    retrieval through Milvus replaces the substring step in the RAG
    retriever layer; confidence + time ordering remain as final tiebreakers.

    Returns parallel lists of (db ids, domain claims) so callers can log
    which DB rows were retrieved and which subset was cited.
    """
    q_lower = (query or "").lower().strip()
    stmt = select(EvidenceClaimRow).where(EvidenceClaimRow.ingest_id == ingest_id)
    if channels:
        stmt = stmt.where(EvidenceClaimRow.channel.in_(channels))
    if q_lower:
        substr_match = func.lower(EvidenceClaimRow.claim_text).like(f"%{q_lower}%")
        substr_rank = case((substr_match, 1), else_=0)
        stmt = stmt.order_by(
            substr_rank.desc(),
            _CONFIDENCE_RANK.desc(),
            EvidenceClaimRow.start_sec.asc(),
        )
    else:
        stmt = stmt.order_by(
            _CONFIDENCE_RANK.desc(),
            EvidenceClaimRow.start_sec.asc(),
        )
    stmt = stmt.limit(limit)
    rows = list((await session.scalars(stmt)).all())
    return [r.id for r in rows], [_row_to_domain(r) for r in rows]


# === Same-layer conflict detection ===


def _time_iou(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    inter_start = max(a_start, b_start)
    inter_end = min(a_end, b_end)
    if inter_end <= inter_start:
        return 0.0
    union_start = min(a_start, b_start)
    union_end = max(a_end, b_end)
    union = union_end - union_start
    if union <= 0:
        return 0.0
    return (inter_end - inter_start) / union


def detect_same_layer_conflicts(
    claims: list[EvidenceClaim],
    *,
    min_iou: float = 0.3,
) -> list[str]:
    """Detect same-layer (same channel) time-overlapping disagreement.

    Two claims in the same channel, with IoU >= `min_iou`, different
    `source_tool`, and non-identical text -> emit one flag string.
    Detection does not block the pipeline; flags are passed to the
    integrator so it can reason about them in its `inference_chain`.
    """
    by_channel: dict[str, list[tuple[int, EvidenceClaim]]] = defaultdict(list)
    for i, c in enumerate(claims):
        by_channel[c.channel].append((i, c))

    flags: list[str] = []
    for channel, items in by_channel.items():
        n = len(items)
        for ai in range(n):
            for bi in range(ai + 1, n):
                ia, ca = items[ai]
                ib, cb = items[bi]
                if ca.source_tool == cb.source_tool:
                    continue
                iou = _time_iou(
                    ca.time_range.start, ca.time_range.end,
                    cb.time_range.start, cb.time_range.end,
                )
                if iou < min_iou:
                    continue
                if ca.claim_text.strip() == cb.claim_text.strip():
                    continue
                flags.append(
                    f"channel={channel} [{ia}] vs [{ib}] "
                    f"iou={iou:.2f} "
                    f"texts={ca.claim_text[:60]!r} vs {cb.claim_text[:60]!r}"
                )
    return flags


# === Query logging ===


async def log_query(
    session: AsyncSession,
    *,
    ingest_id: str,
    query_text: str,
    answer: str | None,
    status: str,
    abstain_kind: str | None,
    abstain_reason: str | None,
    trace: str,
    llm_provider: str | None,
    llm_model: str | None,
    retrieved_evidence_ids: list[str],
    cited_indices: list[int],
) -> str:
    query_id = str(uuid.uuid4())
    log_row = QueryLog(
        id=query_id,
        ingest_id=ingest_id,
        query_text=query_text,
        answer=answer,
        status=status,
        abstain_kind=abstain_kind,
        abstain_reason=abstain_reason,
        trace=trace,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    session.add(log_row)
    cited_set = set(cited_indices)
    for rank, ev_id in enumerate(retrieved_evidence_ids):
        session.add(
            QueryEvidenceLog(
                query_id=query_id,
                evidence_id=ev_id,
                was_cited=(rank in cited_set),
                rank=rank,
            )
        )
    await session.flush()
    return query_id


async def list_queries_for_ingest(
    session: AsyncSession, ingest_id: str
) -> list[QueryLog]:
    stmt = (
        select(QueryLog)
        .where(QueryLog.ingest_id == ingest_id)
        .order_by(QueryLog.created_at.desc())
    )
    return list((await session.scalars(stmt)).all())
