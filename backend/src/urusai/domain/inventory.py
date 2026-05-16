"""Content inventory schema — cheap probe report from the ingest stage.

The probe decides which channels can contribute evidence for the current
video. The query stage uses this to do inventory-aware dispatch and
structural abstain: a query that targets a channel the video does not have
returns an abstain without escalating.
"""
from pydantic import BaseModel, Field


class ChannelAvailability(BaseModel):
    """Whether each channel has substantive content for the current video."""

    has_audio: bool = False
    has_speech: bool = False
    has_music: bool = False
    has_visual: bool = True
    visual_static: bool = False
    has_manual_subs: bool = False
    subs_lang: str | None = None
    duration_sec: float = 0.0


class InventoryReport(BaseModel):
    """Inventory probe report from the ingest stage, consumed by the channel dispatcher."""

    video_id: str
    source_path: str
    inventory: ChannelAvailability
    dispatched_channels: list[str] = Field(default_factory=list)
    skipped_channels: dict[str, str] = Field(default_factory=dict)
