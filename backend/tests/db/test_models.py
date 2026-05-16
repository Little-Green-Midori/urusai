"""Schema sanity tests — no DB connection required."""
from __future__ import annotations

from urusai.db.models import (
    Base,
    EvidenceClaim,
    Ingest,
    QueryEvidenceLog,
    QueryLog,
)


def test_metadata_has_expected_tables():
    assert set(Base.metadata.tables.keys()) == {
        "ingests",
        "evidence_claims",
        "query_log",
        "query_evidence_log",
    }


def test_ingests_columns():
    cols = {c.name for c in Ingest.__table__.columns}
    expected = {
        "id",
        "source_path",
        "url",
        "video_id",
        "inventory",
        "status",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(cols), expected - cols


def test_evidence_claims_columns():
    cols = {c.name for c in EvidenceClaim.__table__.columns}
    expected = {
        "id",
        "ingest_id",
        "channel",
        "start_sec",
        "end_sec",
        "claim_text",
        "raw_quote",
        "confidence",
        "source_tool",
        "source_spec",
        "inference_strength",
        "inference_chain",
        "extra_metadata",
        "created_at",
    }
    assert expected.issubset(cols), expected - cols


def test_query_log_columns():
    cols = {c.name for c in QueryLog.__table__.columns}
    expected = {
        "id",
        "ingest_id",
        "query_text",
        "answer",
        "status",
        "abstain_kind",
        "abstain_reason",
        "trace",
        "llm_provider",
        "llm_model",
        "created_at",
    }
    assert expected.issubset(cols), expected - cols


def test_query_evidence_log_columns():
    cols = {c.name for c in QueryEvidenceLog.__table__.columns}
    expected = {"id", "query_id", "evidence_id", "was_cited", "rank"}
    assert expected.issubset(cols), expected - cols


def test_evidence_claim_indexed_columns():
    indexed = {
        c.name for c in EvidenceClaim.__table__.columns if c.index
    }
    assert {"ingest_id", "channel", "start_sec"}.issubset(indexed)


def test_channel_is_string_not_enum():
    """Channel-open schema: `channel` is a plain string, not an enum type."""
    from sqlalchemy import Enum, String

    col = EvidenceClaim.__table__.columns["channel"]
    assert isinstance(col.type, String)
    assert not isinstance(col.type, Enum)
