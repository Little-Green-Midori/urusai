"""場景本 channel —— PySceneDetect content detector → scene boundaries。

Phase 1：只切時間邊界、不含 caption。caption 之後接 VLM channel 補。
"""
from __future__ import annotations

from scenedetect import ContentDetector, detect

from urusai.domain.evidence import ConfidenceMarker, EvidenceClaim, TimeRange


DEFAULT_THRESHOLD = 27.0


class SceneChannel:
    """場景本 from PySceneDetect content detector。"""

    name = "scene"

    def __init__(self, threshold: float = DEFAULT_THRESHOLD) -> None:
        self.threshold = threshold

    async def extract(
        self, source_path: str, **kwargs: object
    ) -> list[EvidenceClaim]:
        scene_list = detect(source_path, ContentDetector(threshold=self.threshold))
        claims: list[EvidenceClaim] = []
        for i, (start, end) in enumerate(scene_list):
            start_sec = float(start.get_seconds())
            end_sec = float(end.get_seconds())
            if end_sec <= start_sec:
                continue
            claims.append(
                EvidenceClaim(
                    channel="scene",
                    time_range=TimeRange(start=start_sec, end=end_sec),
                    claim_text=f"scene {i + 1}",
                    raw_quote=None,
                    confidence=ConfidenceMarker.CLEAR,
                    source_tool=f"PySceneDetect:ContentDetector:t={self.threshold}",
                )
            )
        return claims
