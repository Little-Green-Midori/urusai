"""URUSAI agent package — LangGraph 1.x state machine.

Public surface:
- `AgentState` — state schema (urusai.agent.state)
- `build_graph(dsn)` — compile + return checkpointed graph (urusai.agent.graph)
- `encode_sse_event`, `make_event_id` — SSE Data Stream Protocol helpers (urusai.agent.stream)
"""
from urusai.agent.state import AgentState

__all__ = ["AgentState"]
