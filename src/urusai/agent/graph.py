"""Agent runner —— Phase 1 sequential（orchestrator → integrator）。

LangGraph state machine 在 Phase 2+ 加（有 conditional cycle 才需要）。
"""
from __future__ import annotations

from urusai.agent.nodes import integrator_node, orchestrator_node
from urusai.agent.state import AgentState
from urusai.store.ingest_store import IngestState


def run_query(query: str, ingest: IngestState) -> AgentState:
    """Phase 1 query 入口：rule-based orchestrator → LLM integrator。"""
    state = AgentState(query=query)
    state = orchestrator_node(state, ingest)
    if state.abstain_kind == "structural":
        return state
    state = integrator_node(state, ingest)
    return state
