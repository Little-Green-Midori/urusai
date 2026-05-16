"""ASR channel — providers register at import time."""
from urusai.channels.asr.faster_whisper import (
    FasterWhisperASR,
    FasterWhisperConfig,
)

# Backward-compat aliases for callers that still import the legacy names.
ASRChannel = FasterWhisperASR

__all__ = ["FasterWhisperASR", "FasterWhisperConfig", "ASRChannel"]
