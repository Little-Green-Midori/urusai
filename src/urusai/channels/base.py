"""Channel protocol —— 所有工具 channel 的共同介面。

每個 channel 從 video / audio segment 抽 EvidenceClaim list、產出投到對應筆記。
"""
from pathlib import Path
from typing import Protocol

from urusai.domain.evidence import EvidenceClaim


class Channel(Protocol):
    name: str

    async def extract(
        self, source: Path, time_range: tuple[float, float] | None = None, **kwargs
    ) -> list[EvidenceClaim]: ...
