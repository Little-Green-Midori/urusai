"""initial schema: ingests / evidence_claims / query_log / query_evidence_log

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-13

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingests",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("video_id", sa.String(length=64), nullable=False),
        sa.Column("inventory", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="ready",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "evidence_claims",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "ingest_id",
            sa.String(length=64),
            sa.ForeignKey("ingests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("start_sec", sa.Float(), nullable=False),
        sa.Column("end_sec", sa.Float(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("raw_quote", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("source_tool", sa.Text(), nullable=False),
        sa.Column(
            "source_spec",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("inference_strength", sa.String(length=16), nullable=True),
        sa.Column(
            "inference_chain",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "extra_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_evidence_claims_ingest_id", "evidence_claims", ["ingest_id"]
    )
    op.create_index(
        "ix_evidence_claims_channel", "evidence_claims", ["channel"]
    )
    op.create_index(
        "ix_evidence_claims_start_sec", "evidence_claims", ["start_sec"]
    )

    op.create_table(
        "query_log",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "ingest_id",
            sa.String(length=64),
            sa.ForeignKey("ingests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("abstain_kind", sa.String(length=32), nullable=True),
        sa.Column("abstain_reason", sa.Text(), nullable=True),
        sa.Column("trace", sa.Text(), nullable=False),
        sa.Column("llm_provider", sa.String(length=64), nullable=True),
        sa.Column("llm_model", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_query_log_ingest_id", "query_log", ["ingest_id"])

    op.create_table(
        "query_evidence_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "query_id",
            sa.String(length=36),
            sa.ForeignKey("query_log.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evidence_id",
            sa.String(length=36),
            sa.ForeignKey("evidence_claims.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "was_cited",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_query_evidence_log_query_id", "query_evidence_log", ["query_id"]
    )
    op.create_index(
        "ix_query_evidence_log_evidence_id",
        "query_evidence_log",
        ["evidence_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_query_evidence_log_evidence_id", table_name="query_evidence_log"
    )
    op.drop_index(
        "ix_query_evidence_log_query_id", table_name="query_evidence_log"
    )
    op.drop_table("query_evidence_log")
    op.drop_index("ix_query_log_ingest_id", table_name="query_log")
    op.drop_table("query_log")
    op.drop_index(
        "ix_evidence_claims_start_sec", table_name="evidence_claims"
    )
    op.drop_index("ix_evidence_claims_channel", table_name="evidence_claims")
    op.drop_index(
        "ix_evidence_claims_ingest_id", table_name="evidence_claims"
    )
    op.drop_table("evidence_claims")
    op.drop_table("ingests")
