"""Retriever node — Milvus hybrid search + SQL tiebreaker.

Retriever node: pure read path, no interrupt(). Pulls evidence claims via the hybrid retriever and ranks them.
"""
from __future__ import annotations

from urusai.agent.state import AgentState


async def retriever_node(state: AgentState) -> dict:
    """Run hybrid retrieval, populate retrieved_evidence + conflict_flags."""
    if state.abstain_kind == "structural":
        return {}
    if state.ingest_id is None:
        return {}

    # TODO: implement
    # 1) embed query via urusai.rag.embedder.embed_text
    # 2) urusai.rag.retriever.hybrid_search(collection=urusai_v_<ingest_id>, ...)
    # 3) SQL tiebreaker against evidence_claims
    # 4) detect same-layer conflict -> conflict_flags
    return {
        "retrieved_evidence": [],
        "retrieved_evidence_ids": [],
        "conflict_flags": [],
    }
