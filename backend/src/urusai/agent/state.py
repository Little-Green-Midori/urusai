"""AgentState — LangGraph state schema.

AgentState extends the original single-purpose
AgentState with a fuller schema that covers HITL interrupts, escalation,
and the multi-channel observer routing decision.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from urusai.domain.evidence import EvidenceClaim
from urusai.domain.inventory import InventoryReport
from urusai.providers.select import ProviderSelection


AbstainKind = Literal[
    "structural",
    "evidence_insufficient",
    "conflict_unresolvable",
    "rate_limit_mid_stream",
]

InferenceStrength = Literal["observation", "strong", "weak"]


class ChannelDispatch(BaseModel):
    """Observer-emitted channel routing decision.

    LaneScheduler reads `lane` from provider; observer decides `priority` from
    query relevance + cost.
    """

    channel: str
    provider: str
    priority: int = 0
    reason: str = ""


class AgentState(BaseModel):
    """LangGraph thread state.

    A single AgentState instance lives per `thread_id`; LangGraph checkpoints
    it at every node boundary. For idempotency, any node containing
    interrupt() must keep side-effects idempotent.
    """

    query: str = ""
    ingest_id: str | None = None
    inventory: InventoryReport | None = None
    provider_selection: ProviderSelection = Field(default_factory=ProviderSelection)

    dispatched_channels: list[ChannelDispatch] = Field(default_factory=list)
    required_channels: list[str] = Field(default_factory=list)

    retrieved_evidence: list[EvidenceClaim] = Field(default_factory=list)
    retrieved_evidence_ids: list[str] = Field(default_factory=list)
    conflict_flags: list[str] = Field(default_factory=list)

    escalation_history: list[dict[str, Any]] = Field(default_factory=list)
    escalation_count: int = 0

    cited_indices: list[int] = Field(default_factory=list)
    inference_chain: list[str] = Field(default_factory=list)
    inference_strength: InferenceStrength | None = None
    final_answer: str | None = None

    abstain_kind: AbstainKind | None = None
    abstain_reason: str | None = None

    run_id: str = ""
    event_seq: int = 0

    history: list[dict[str, Any]] = Field(default_factory=list)


MAX_TURNS = 10
