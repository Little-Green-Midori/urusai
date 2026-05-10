"""Ingest state store —— Phase 1 in-memory dict。

每次 ingest 一支影片產生一個 IngestState、後續 query 用 ingest_id 找回來。
Phase 1 in-memory；Phase 2+ 可換 SQLite / disk persist。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from urusai.domain.evidence import EvidenceClaim
from urusai.domain.graph import StaticGraph
from urusai.domain.inventory import InventoryReport
from urusai.domain.notebook import (
    DialogueNotebook,
    HolisticNotebook,
    OnScreenTextNotebook,
    SceneNotebook,
    SoundEventNotebook,
)
from urusai.domain.time_axis import TimeAxis


@dataclass
class IngestState:
    ingest_id: str
    inventory: InventoryReport
    dialogue: DialogueNotebook = field(default_factory=DialogueNotebook)
    on_screen_text: OnScreenTextNotebook = field(default_factory=OnScreenTextNotebook)
    scene: SceneNotebook = field(default_factory=SceneNotebook)
    sound_event: SoundEventNotebook = field(default_factory=SoundEventNotebook)
    holistic: HolisticNotebook = field(default_factory=HolisticNotebook)
    time_axis: TimeAxis = field(default_factory=TimeAxis)
    static_graph: StaticGraph = field(default_factory=StaticGraph)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def notebook_by_name(self, name: str) -> Any:
        mapping = {
            "dialogue": self.dialogue,
            "on_screen_text": self.on_screen_text,
            "scene": self.scene,
            "sound_event": self.sound_event,
            "holistic": self.holistic,
        }
        return mapping.get(name)

    def absorb(self, claims: list[EvidenceClaim]) -> int:
        """把 channel 出來的 claims 落到對應 notebook + time_axis。回傳吸收數。"""
        absorbed = 0
        for claim in claims:
            nb = self.notebook_by_name(claim.channel)
            if nb is None:
                continue
            nb.append(claim)
            self.time_axis.add(claim)
            absorbed += 1
        return absorbed

    def notebook_summary(self) -> dict[str, int]:
        return {
            "dialogue": len(self.dialogue.all_claims()),
            "on_screen_text": len(self.on_screen_text.all_claims()),
            "scene": len(self.scene.all_claims()),
            "sound_event": len(self.sound_event.all_claims()),
            "holistic": len(self.holistic.all_claims()),
        }


class IngestStore:
    """Process-local in-memory store——thread-safe via single lock。"""

    def __init__(self) -> None:
        self._states: dict[str, IngestState] = {}
        self._lock = Lock()

    def put(self, state: IngestState) -> None:
        with self._lock:
            self._states[state.ingest_id] = state

    def get(self, ingest_id: str) -> IngestState | None:
        with self._lock:
            return self._states.get(ingest_id)

    def list_ids(self) -> list[str]:
        with self._lock:
            return list(self._states.keys())

    def delete(self, ingest_id: str) -> bool:
        with self._lock:
            return self._states.pop(ingest_id, None) is not None


_default_store: IngestStore | None = None


def get_default_store() -> IngestStore:
    global _default_store
    if _default_store is None:
        _default_store = IngestStore()
    return _default_store
