"""API request / response schemas —— Phase 1。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from urusai.domain.inventory import InventoryReport


class IngestRequest(BaseModel):
    file_path: str | None = None
    url: str | None = None
    video_id: str | None = None


class IngestResponse(BaseModel):
    ingest_id: str
    inventory: InventoryReport
    notebooks: dict[str, int]


class EvidenceItem(BaseModel):
    index: int
    channel: str
    start_sec: float
    end_sec: float
    text: str
    source_tool: str


class QueryRequest(BaseModel):
    ingest_id: str
    query: str


class QueryResponse(BaseModel):
    status: Literal["answered", "abstain"]
    answer: str | None = None
    cited_evidence: list[EvidenceItem] = Field(default_factory=list)
    abstain_kind: str | None = None
    abstain_reason: str | None = None
    trace: str
