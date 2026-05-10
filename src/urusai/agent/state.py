"""Agent state —— Phase 1 query loop 狀態。

Phase 1 sequential：orchestrator（rule-based dispatch）→ integrator（LLM call）。
LangGraph state machine 留待 Phase 2+（有 conditional cycle 才需要）。
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from urusai.domain.evidence import EvidenceClaim


AbstainKind = Literal["structural", "evidence_insufficient"]


class AgentState(BaseModel):
    query: str
    retrieved_evidence: list[EvidenceClaim] = Field(default_factory=list)
    cited_indices: list[int] = Field(default_factory=list)
    final_answer: str | None = None
    abstain_kind: AbstainKind | None = None
    abstain_reason: str | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)


MAX_TURNS = 10
