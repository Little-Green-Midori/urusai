"""PySceneDetect scene boundary provider."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from scenedetect import ContentDetector, detect

from urusai.channels.base import ChannelSpec
from urusai.channels.registry import ChannelRegistry
from urusai.domain.evidence import ConfidenceMarker, EvidenceClaim, TimeRange


class PySceneDetectConfig(BaseModel):
    threshold: float = Field(default=27.0, ge=1.0, le=100.0)


@ChannelRegistry.register(channel="scene", name="pyscenedetect")
class PySceneDetectScene:
    """PySceneDetect ContentDetector → scene boundary EvidenceClaims."""

    name = "pyscenedetect"
    channel = "scene"
    config_class = PySceneDetectConfig

    def __init__(self, config: PySceneDetectConfig | None = None) -> None:
        self.config = config or PySceneDetectConfig()

    def unload(self) -> None:
        return None

    async def extract(self, source_path: Path | str) -> list[EvidenceClaim]:
        scene_list = detect(
            str(source_path),
            ContentDetector(threshold=self.config.threshold),
        )
        spec = ChannelSpec(
            channel="scene",
            provider=self.name,
            config=self.config.model_dump(),
        )
        source_tool = f"PySceneDetect:ContentDetector:t={self.config.threshold}"

        claims: list[EvidenceClaim] = []
        for i, (start, end) in enumerate(scene_list):
            start_sec = float(start.get_seconds())
            end_sec = float(end.get_seconds())
            if end_sec <= start_sec:
                continue
            claims.append(
                EvidenceClaim(
                    channel=self.channel,
                    time_range=TimeRange(start=start_sec, end=end_sec),
                    claim_text=f"scene {i + 1}",
                    raw_quote=None,
                    confidence=ConfidenceMarker.CLEAR,
                    source_tool=source_tool,
                    source_spec=spec,
                )
            )
        return claims
