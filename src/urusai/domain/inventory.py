"""Content inventory schema —— ingest 階段 cheap probe 結果報告。

probe 出哪幾本筆記能填、agent query 階段才能用 inventory-aware dispatch +
結構性 abstain（query 對沒這層的影片直接 abstain、不浪費 escalate）。
"""
from pydantic import BaseModel, Field


class ChannelAvailability(BaseModel):
    """各 channel 是否有實質內容可填。"""

    has_audio: bool = False
    has_speech: bool = False
    has_music: bool = False
    has_visual: bool = True
    visual_static: bool = False
    has_manual_subs: bool = False
    subs_lang: str | None = None
    duration_sec: float = 0.0


class InventoryReport(BaseModel):
    """ingest 階段 inventory probe 報告——driver 給 channel dispatcher 用。"""

    video_id: str
    source_path: str
    inventory: ChannelAvailability
    dispatched_channels: list[str] = Field(default_factory=list)
    skipped_channels: dict[str, str] = Field(default_factory=dict)
