"""Integrator node — LLM answer + cite/chain/strength schema enforcement.

Integrator node: composes the final answer from retrieved evidence.

- Strict schema: status="answered" MUST include answer + cited_evidence_indices
  + inference_chain + inference_strength. Any missing field rewrites to abstain.
- Chat mode: integrator runs with chat_persona prompt, no evidence.

Mid-stream rate limit handling: emit partial + error, do not hot-swap providers.
- TTFT-pre 429: silently retry rotator.acquire() (next token)
- TTFT-post 429: abort run, emit data-error event, status=failed_mid_stream

Idempotency: NO writes before any interrupt; SSE emits via deterministic
event_id + UPSERT.
"""
from __future__ import annotations

from urusai.agent.state import AgentState


async def integrator_node(state: AgentState) -> dict:
    """LLM integration with strict schema; updates final_answer + cite chain."""
    if state.abstain_kind == "structural":
        return {}

    # TODO: implement
    # 1) build messages: system_prompt (integrator_system.md) + user prompt
    # 2) acquire LLM provider via providers.resolve_provider
    # 3) acquire token via rotator
    # 4) stream_chat -> collect cited_indices, inference_chain, inference_strength
    # 5) validate strict schema; missing field -> abstain_kind="evidence_insufficient"
    # 6) emit SSE text-delta events via stream.encode_sse_event

    return {
        "final_answer": None,
        "cited_indices": [],
        "inference_chain": [],
        "inference_strength": None,
    }
