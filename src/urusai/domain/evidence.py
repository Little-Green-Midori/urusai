"""Evidence claim schema —— atomic 單位。

每個 final answer 都帶 evidence trace、最小單位是 EvidenceClaim：
- 來自哪本筆記（channel）
- 哪個時段（time_range）
- claim 內容 + 原始 quote
- 學生自標的信心等級（觀察類）
- 推論強度 + 推論鏈（推論類）
"""
from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceMarker(str, Enum):
    CLEAR = "clear"
    BLURRY = "blurry"
    INFERRED = "inferred"


class InferenceStrength(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    GUESS = "guess"


class TimeRange(BaseModel):
    start: float = Field(..., ge=0)
    end: float = Field(..., ge=0)


class EvidenceClaim(BaseModel):
    channel: str
    time_range: TimeRange
    claim_text: str
    raw_quote: str | None = None
    confidence: ConfidenceMarker
    source_tool: str
    inference_strength: InferenceStrength | None = None
    inference_chain: list[str] | None = None
