"""共同時間軸 substrate.

所有 channel evidence 投到統一時間 bin、跨 channel agreement / conflict 都在 bin 內 reason。

容忍各 channel 不確定範圍：
- ASR / OCR per-frame: ms-level
- Scene boundary / audio event: second-level
- VLM 自報: 飄秒到分鐘級
"""
from intervaltree import IntervalTree

from .evidence import EvidenceClaim


DEFAULT_BIN_SECONDS = 0.5


class TimeAxis:
    """所有 evidence claim 落在共同時間軸、用 IntervalTree 索引。"""

    def __init__(self, bin_seconds: float = DEFAULT_BIN_SECONDS) -> None:
        self.bin_seconds = bin_seconds
        self._tree: IntervalTree = IntervalTree()

    def add(self, claim: EvidenceClaim) -> None:
        s = claim.time_range.start
        e = claim.time_range.end
        if e <= s:
            e = s + 1e-9
        self._tree.addi(s, e, claim)

    def at(self, t: float) -> list[EvidenceClaim]:
        return [iv.data for iv in self._tree.at(t)]

    def overlap(self, start: float, end: float) -> list[EvidenceClaim]:
        return [iv.data for iv in self._tree.overlap(start, end)]

    def all_at_bin(self, t: float) -> list[EvidenceClaim]:
        s = (t // self.bin_seconds) * self.bin_seconds
        e = s + self.bin_seconds
        return self.overlap(s, e)
