"""Channel / Provider base types.

A **channel** is a concept ("ASR", "scene detection", "OCR", ...). A **provider**
is a concrete implementation of that concept (faster-whisper, OpenAI Whisper API,
PySceneDetect, ...). Each provider declares its own `config_class` (Pydantic
model) describing the tunable parameters.

`ChannelSpec` (re-exported here for convenience) lives in `urusai.domain.evidence`
so it can be a field on `EvidenceClaim` without crossing the domain ← channels
dependency boundary.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from urusai.domain.evidence import ChannelSpec, EvidenceClaim


@runtime_checkable
class Provider(Protocol):
    """Channel provider contract.

    Each concrete provider is registered against a channel concept via
    `ChannelRegistry.register(channel=..., name=...)` and produces
    `EvidenceClaim`s tagged with the provider's declared `channel`.
    """

    name: str
    channel: str
    config_class: type[BaseModel]

    async def extract(self, source_path: Path | str) -> list[EvidenceClaim]:
        ...

    def unload(self) -> None:
        ...


__all__ = ["Provider", "ChannelSpec"]
