"""Observer node — load inventory + decide channel routing.

Observer node: read-only inventory probe + channel dispatch decision.

Responsibilities:
1. Load InventoryReport (passed in or fetched from DB by ingest_id)
2. Classify query (cheap LLM or heuristic) into required_channels
3. Cross-check inventory: if required not a subset of available, set abstain_kind=structural
4. Emit dispatched_channels with priority + reason
5. Chat mode (no ingest_id): skip channel routing, integrator passthrough

Idempotency: side effects (DB writes) must go AFTER any interrupt call,
or use deterministic UPSERT.
"""
from __future__ import annotations

from urusai.agent.state import AgentState


async def observer_node(state: AgentState) -> dict:
    """Inspect query + inventory; emit ChannelDispatch list or structural abstain."""
    if state.ingest_id is None:
        return {
            "dispatched_channels": [],
            "required_channels": [],
        }

    # TODO: implement
    # 1) classify query -> required_channels
    # 2) cross-check inventory: structural abstain if required not in inventory
    # 3) emit ChannelDispatch list (channel, provider, priority, reason)
    return {}
