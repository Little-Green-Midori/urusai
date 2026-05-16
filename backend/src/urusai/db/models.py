"""SQLAlchemy ORM models for urusai persistence.

Channel-open schema: `channel` is a plain string with no enum constraint, so
new channels can be added without DDL migration. Channel-specific data lives
in the JSONB `extra_metadata` column.

run_events + job_events tables
support SSE Data Stream Protocol resumability + interrupt resume idempotency
via deterministic event_id + ON CONFLICT DO NOTHING.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Ingest(Base):
    __tablename__ = "ingests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_path: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_id: Mapped[str] = mapped_column(String(64))
    inventory: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), default="ready")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    evidence: Mapped[list[EvidenceClaim]] = relationship(
        back_populates="ingest", cascade="all, delete-orphan"
    )
    queries: Mapped[list[QueryLog]] = relationship(
        back_populates="ingest", cascade="all, delete-orphan"
    )


class EvidenceClaim(Base):
    __tablename__ = "evidence_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ingest_id: Mapped[str] = mapped_column(
        ForeignKey("ingests.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(32), index=True)
    start_sec: Mapped[float] = mapped_column(Float, index=True)
    end_sec: Mapped[float] = mapped_column(Float)
    claim_text: Mapped[str] = mapped_column(Text)
    raw_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(16))
    source_tool: Mapped[str] = mapped_column(Text)
    source_spec: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    inference_strength: Mapped[str | None] = mapped_column(String(16), nullable=True)
    inference_chain: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ingest: Mapped[Ingest] = relationship(back_populates="evidence")


class QueryLog(Base):
    __tablename__ = "query_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ingest_id: Mapped[str] = mapped_column(
        ForeignKey("ingests.id", ondelete="CASCADE"), index=True
    )
    query_text: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16))
    abstain_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    abstain_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace: Mapped[str] = mapped_column(Text)
    llm_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ingest: Mapped[Ingest] = relationship(back_populates="queries")
    evidence_links: Mapped[list[QueryEvidenceLog]] = relationship(
        back_populates="query", cascade="all, delete-orphan"
    )


class QueryEvidenceLog(Base):
    __tablename__ = "query_evidence_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(
        ForeignKey("query_log.id", ondelete="CASCADE"), index=True
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_claims.id", ondelete="CASCADE"), index=True
    )
    was_cited: Mapped[bool] = mapped_column(Boolean, default=False)
    rank: Mapped[int] = mapped_column(Integer)

    query: Mapped[QueryLog] = relationship(back_populates="evidence_links")


class RunEvent(Base):
    """SSE event log for /v1/threads/{id}/runs/{run_id}/events resumability.

    PRIMARY KEY (run_id, event_id) + ON CONFLICT DO NOTHING on writes
    means interrupt() resume re-execution does not double-emit.
    """

    __tablename__ = "run_events"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class JobEvent(Base):
    """SSE event log for /v1/jobs/{job_id}/events (ingest progress).

    Same deterministic event_id + ON CONFLICT discipline as RunEvent.
    """

    __tablename__ = "job_events"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
