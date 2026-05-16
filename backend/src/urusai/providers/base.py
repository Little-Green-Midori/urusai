"""Provider Protocol contracts per modality.

Imported by:
- `urusai.providers.{llm,vlm,asr,ocr,diarization,audio_event,mss,embedding}.*` (provider impls)
- `urusai.providers.select` (resolve_provider)
- `urusai.ingest.scheduler` (lane assignment)

Provider Protocols for every channel + lane assignment for the scheduler.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

from urusai.domain.evidence import EvidenceClaim


# Lane assignments — used by the ingest scheduler to bound parallelism per resource class.
# LaneScheduler reads `provider.lane` to decide which semaphore the work belongs to.
Lane = Literal["gpu_heavy", "gpu_medium", "cpu", "external", "api", "io"]


class ChatChunk(BaseModel):
    """Single chunk of a streaming chat response."""

    delta: str = ""
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class ChatResult(BaseModel):
    """Non-streaming chat response."""

    text: str
    finish_reason: str
    usage: dict[str, int] = {}


class OCRSpan(BaseModel):
    """Single OCR-recognised text span with bounding box."""

    text: str
    bbox: tuple[float, float, float, float]  # (x1, y1, x2, y2) normalised 0..1
    confidence: float


class VLMResult(BaseModel):
    """LVLM clip describe / question result."""

    description: str
    confidence: float
    raw: dict[str, Any] | None = None


class SpeakerSegment(BaseModel):
    """Single contiguous speaker segment from diarization."""

    speaker_id: str
    start_sec: float
    end_sec: float


class AudioEvent(BaseModel):
    """Single sound-event detection hit."""

    label: str
    start_sec: float
    end_sec: float
    confidence: float


@runtime_checkable
class LLMProvider(Protocol):
    """Text / multimodal LLM provider (chat + streaming)."""

    name: str
    lane: Lane
    capabilities: frozenset[str]
    config_class: type[BaseModel]

    async def chat(self, messages: list[dict], **kw: Any) -> ChatResult: ...
    async def stream_chat(self, messages: list[dict], **kw: Any) -> AsyncIterator[ChatChunk]: ...
    def unload(self) -> None: ...


@runtime_checkable
class ASRProvider(Protocol):
    """Speech-to-text provider."""

    name: str
    lane: Lane
    config_class: type[BaseModel]

    async def transcribe(
        self, audio_path: Path, lang: str | None = None
    ) -> list[EvidenceClaim]: ...
    def unload(self) -> None: ...


@runtime_checkable
class OCRProvider(Protocol):
    """Image-to-text provider (no language model reasoning)."""

    name: str
    lane: Lane

    async def extract(self, image_path: Path) -> list[OCRSpan]: ...
    def unload(self) -> None: ...


@runtime_checkable
class VLMProvider(Protocol):
    """Vision LLM provider — describe a clip / answer a vision question."""

    name: str
    lane: Lane

    async def describe(self, clip_path: Path, prompt: str) -> VLMResult: ...
    def unload(self) -> None: ...


@runtime_checkable
class DiarizationProvider(Protocol):
    """Who-said-what provider."""

    name: str
    lane: Lane

    async def diarize(
        self, audio_path: Path, num_speakers: int | None = None
    ) -> list[SpeakerSegment]: ...
    def unload(self) -> None: ...


@runtime_checkable
class AudioEventProvider(Protocol):
    """Non-speech audio event detection (SED)."""

    name: str
    lane: Lane

    async def detect(self, audio_path: Path) -> list[AudioEvent]: ...
    def unload(self) -> None: ...


@runtime_checkable
class MSSProvider(Protocol):
    """Music / vocal source separation."""

    name: str
    lane: Lane

    async def separate(self, audio_path: Path) -> dict[str, Path]: ...
    def unload(self) -> None: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Multimodal embedder (text / image / video / audio)."""

    name: str
    lane: Lane
    output_dim: int
    modalities: frozenset[str]

    async def embed(self, content: Any, modality: str) -> list[float]: ...
