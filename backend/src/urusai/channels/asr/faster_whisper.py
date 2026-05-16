"""faster-whisper local ASR provider."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from faster_whisper import WhisperModel
from pydantic import BaseModel, Field

from urusai.channels.base import ChannelSpec
from urusai.channels.registry import ChannelRegistry
from urusai.domain.evidence import ConfidenceMarker, EvidenceClaim, TimeRange


LOGPROB_CLEAR_THRESHOLD = -0.7

ModelSize = Literal["large-v3-turbo", "large-v3", "medium", "small", "base", "tiny"]
Device = Literal["cuda", "cpu"]
ComputeType = Literal["float16", "int8", "int8_float16", "float32"]


class FasterWhisperConfig(BaseModel):
    model_size: ModelSize = "large-v3-turbo"
    device: Device = "cuda"
    compute_type: ComputeType = "float16"
    beam_size: int = Field(default=5, ge=1, le=10)
    vad_filter: bool = True
    language: str | None = Field(
        default=None, description="ISO language code; None for auto-detect"
    )


@ChannelRegistry.register(channel="asr", name="faster-whisper")
class FasterWhisperASR:
    """faster-whisper local ASR; emits `dialogue`-channel claims."""

    name = "faster-whisper"
    channel = "dialogue"
    config_class = FasterWhisperConfig

    def __init__(self, config: FasterWhisperConfig | None = None) -> None:
        self.config = config or FasterWhisperConfig()
        self._model: WhisperModel | None = None

    def _ensure_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type,
            )
        return self._model

    def unload(self) -> None:
        self._model = None

    async def extract(self, source_path: Path | str) -> list[EvidenceClaim]:
        model = self._ensure_model()
        seg_iter, info = model.transcribe(
            str(source_path),
            language=self.config.language,
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter,
        )
        detected_lang = (info.language or "und") if info is not None else "und"
        spec = ChannelSpec(
            channel="asr",
            provider=self.name,
            config=self.config.model_dump(),
        )
        source_tool = f"faster-whisper:{self.config.model_size}:lang={detected_lang}"

        claims: list[EvidenceClaim] = []
        for seg in seg_iter:
            text = seg.text.strip()
            if not text or seg.end <= seg.start:
                continue
            confident = (
                seg.avg_logprob is not None
                and seg.avg_logprob > LOGPROB_CLEAR_THRESHOLD
            )
            claims.append(
                EvidenceClaim(
                    channel=self.channel,
                    time_range=TimeRange(start=seg.start, end=seg.end),
                    claim_text=text,
                    raw_quote=text,
                    confidence=ConfidenceMarker.CLEAR if confident else ConfidenceMarker.BLURRY,
                    source_tool=source_tool,
                    source_spec=spec,
                )
            )
        return claims
