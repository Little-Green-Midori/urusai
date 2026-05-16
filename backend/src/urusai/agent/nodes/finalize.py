"""Finalize node — serialize trace, write query_log + query_evidence_log.

Finalize node: pure terminal node that serialises the evidence trace and persists the run record.

DB writes use deterministic keys so re-runs of finalize from a forked
checkpoint are idempotent.
"""
from __future__ import annotations

from urusai.agent.state import AgentState


async def finalize_node(state: AgentState) -> dict:
    """Write query_log + query_evidence_log; emit DONE event."""
    # TODO: implement
    # 1) compose trace string (state.final_answer + cited_evidence + inference_chain)
    # 2) UPSERT into query_log (PK = run_id)
    # 3) UPSERT into query_evidence_log (PK = run_id + evidence_id)
    # 4) emit data: [DONE] SSE event
    return {}
