"""Escalator node — channel re-run or external fetch.

Escalator node: invoked when retrieval is empty or conflict-flagged.

External fetch is interrupt()-gated; the user approves before any outbound call.
Side effects (writing escalation_history) MUST go AFTER interrupt call.
"""
from __future__ import annotations

from urusai.agent.state import AgentState


async def escalator_node(state: AgentState) -> dict:
    """Try to fill evidence gaps; may interrupt() for user permission."""
    new_history = list(state.escalation_history)

    # TODO: implement
    # 1) inspect conflict_flags + retrieved_evidence shortfall
    # 2) pick escalation strategy: provider swap | param widen | external fetch
    # 3) if external fetch chosen, interrupt("Allow Jina/Exa fetch for query?")
    #    NOTE: history.append goes AFTER interrupt, not before (H4 idempotency)
    # 4) execute escalation, append to escalation_history

    return {
        "escalation_count": state.escalation_count + 1,
        "escalation_history": new_history,
    }
