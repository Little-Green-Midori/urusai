"""API request / response schemas for the /v1/ resource model.

Resource model:
  Ingest (parsed video) - Job (async operation) - Thread (agent session) - Run (single invocation)
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from urusai.domain.inventory import InventoryReport
from urusai.providers.select import ProviderSelection


# === Ingest ===


class IngestCreateRequest(BaseModel):
    file_path: str | None = None
    url: str | None = None
    video_id: str | None = None
    provider_selection: ProviderSelection = Field(default_factory=ProviderSelection)


class IngestSummary(BaseModel):
    ingest_id: str
    source_path: str
    url: str | None
    video_id: str
    status: str
    created_at: str


class IngestDetail(BaseModel):
    ingest_id: str
    source_path: str
    url: str | None
    video_id: str
    status: str
    inventory: InventoryReport
    evidence_counts: dict[str, int]
    thread_count: int
    created_at: str
    updated_at: str


# === Job ===


class JobStatus(BaseModel):
    job_id: str
    kind: Literal["ingest", "rechannel", "batch_ingest"]
    state: Literal["queued", "running", "succeeded", "failed", "canceled"]
    progress: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: str
    updated_at: str


# === Thread ===


class ThreadCreateRequest(BaseModel):
    ingest_id: str | None = None  # null for chat mode
    title: str | None = None
    provider_selection: ProviderSelection = Field(default_factory=ProviderSelection)


class ThreadSummary(BaseModel):
    thread_id: str
    title: str | None
    ingest_id: str | None
    run_count: int
    created_at: str
    updated_at: str


# === Run ===


class RunCreateRequest(BaseModel):
    message: str | None = None  # chat mode
    query: str | None = None    # grounded mode
    provider_overrides: dict[str, str] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    index: int
    channel: str
    start_sec: float
    end_sec: float
    text: str
    source_tool: str


AbstainKind = Literal[
    "structural",
    "evidence_insufficient",
    "conflict_unresolvable",
    "rate_limit_mid_stream",
]


class RunStatus(BaseModel):
    run_id: str
    thread_id: str
    state: Literal[
        "queued",
        "running",
        "interrupted",
        "succeeded",
        "failed_mid_stream",
        "abstain",
        "canceled",
    ]
    answer: str | None = None
    cited_evidence: list[EvidenceItem] = Field(default_factory=list)
    inference_chain: list[str] = Field(default_factory=list)
    inference_strength: Literal["observation", "strong", "weak"] | None = None
    abstain_kind: AbstainKind | None = None
    abstain_reason: str | None = None
    created_at: str
    completed_at: str | None = None


# === Interrupt ===


class InterruptInfo(BaseModel):
    interrupt_id: str
    payload: dict[str, Any]
    node: str
    ts: str


class InterruptResumeRequest(BaseModel):
    value: Any  # JSON-serializable; passed to Command(resume=value)


# === Webhook ===


class WebhookRegisterRequest(BaseModel):
    url: str
    event_types: list[
        Literal[
            "ingest.completed",
            "ingest.failed",
            "run.completed",
            "run.failed",
            "thread.interrupted",
        ]
    ]
    include_sensitive_payload: bool = False  # opt-in only; minimises egress by default


class WebhookSummary(BaseModel):
    webhook_id: str
    url: str
    event_types: list[str]
    include_sensitive_payload: bool
    created_at: str
