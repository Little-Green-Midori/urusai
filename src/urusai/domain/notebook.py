"""5 本筆記抽象。每本獨立、各記擅長之物、共享時間軸。"""
from typing import Protocol

from .evidence import EvidenceClaim


class Notebook(Protocol):
    name: str

    def append(self, claim: EvidenceClaim) -> None: ...
    def query_by_time(self, start: float, end: float) -> list[EvidenceClaim]: ...
    def all_claims(self) -> list[EvidenceClaim]: ...


class _BaseNotebook:
    name: str = ""

    def __init__(self) -> None:
        self._claims: list[EvidenceClaim] = []

    def append(self, claim: EvidenceClaim) -> None:
        if claim.channel != self.name:
            raise ValueError(
                f"claim channel '{claim.channel}' does not match notebook '{self.name}'"
            )
        self._claims.append(claim)

    def query_by_time(self, start: float, end: float) -> list[EvidenceClaim]:
        return [
            c
            for c in self._claims
            if c.time_range.end >= start and c.time_range.start <= end
        ]

    def all_claims(self) -> list[EvidenceClaim]:
        return list(self._claims)


class DialogueNotebook(_BaseNotebook):
    """對白本——ASR 產出 speech 內容 + word/segment timestamp。"""

    name = "dialogue"


class OnScreenTextNotebook(_BaseNotebook):
    """畫面字本——OCR / LVLM-OCR 讀畫面文字、bbox、per-frame 時間。"""

    name = "on_screen_text"


class SceneNotebook(_BaseNotebook):
    """場景本——scene detection + VLM caption 描述每一場。"""

    name = "scene"


class SoundEventNotebook(_BaseNotebook):
    """聲音本——non-speech 事件（爆炸 / 笑聲 / BGM 變化）。"""

    name = "sound_event"


class HolisticNotebook(_BaseNotebook):
    """整體感本——LVLM clip understanding：跨 frame 動作 / 互動 / narrative。"""

    name = "holistic"
