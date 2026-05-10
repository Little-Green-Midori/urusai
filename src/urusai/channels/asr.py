"""對白本 channel —— faster-whisper local ASR（cuda + float16）。

VRAM ~1.6 GB（large-v3-turbo）。runtime auto-detects language。
"""
from __future__ import annotations

from faster_whisper import WhisperModel

from urusai.domain.evidence import ConfidenceMarker, EvidenceClaim, TimeRange


DEFAULT_MODEL = "large-v3-turbo"
DEFAULT_DEVICE = "cuda"
DEFAULT_COMPUTE_TYPE = "float16"
LOGPROB_CLEAR_THRESHOLD = -0.7


class ASRChannel:
    """faster-whisper local。output 進對白本。"""

    name = "dialogue"

    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
        language: str | None = None,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model: WhisperModel | None = None

    def _ensure_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def unload(self) -> None:
        self._model = None

    async def extract(
        self, source_path: str, **kwargs: object
    ) -> list[EvidenceClaim]:
        model = self._ensure_model()
        lang = kwargs.get("language", self.language)
        seg_iter, info = model.transcribe(
            source_path,
            language=lang if isinstance(lang, str) else None,
            beam_size=5,
            vad_filter=True,
        )
        detected_lang = (info.language or "und") if info is not None else "und"
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
                    channel="dialogue",
                    time_range=TimeRange(start=seg.start, end=seg.end),
                    claim_text=text,
                    raw_quote=text,
                    confidence=ConfidenceMarker.CLEAR if confident else ConfidenceMarker.BLURRY,
                    source_tool=f"faster-whisper:{self.model_size}:lang={detected_lang}",
                )
            )
        return claims
