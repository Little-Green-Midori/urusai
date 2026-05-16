"""Evidence claim schema — atomic unit.

Each final answer carries an evidence trace; the atomic unit is
`EvidenceClaim`, which records:

- which channel produced the claim (`channel`)
- the time range of the underlying observation (`time_range`)
- the claim text + the original raw quote
- a confidence marker (for observation-type claims)
- inference strength + inference chain (for inference-type claims)
- a human-readable source tool string (`source_tool`)
- a structured source spec (`source_spec`)

`source_tool` is the trace-friendly text identifier.
`source_spec` is the structured channel / provider / config triple that
can be serialised, round-tripped, and used to recreate the same provider
configuration.
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


class ChannelSpec(BaseModel):
    """Serialised channel + provider + config triple."""

    channel: str = Field(..., description="Channel concept name (asr / scene / ocr / ...)")
    provider: str = Field(..., description="Provider name within the channel")
    config: dict = Field(default_factory=dict, description="Provider-specific config dump")


class EvidenceClaim(BaseModel):
    channel: str
    time_range: TimeRange
    claim_text: str
    raw_quote: str | None = None
    confidence: ConfidenceMarker
    source_tool: str
    source_spec: ChannelSpec | None = None
    inference_strength: InferenceStrength | None = None
    inference_chain: list[str] | None = None
