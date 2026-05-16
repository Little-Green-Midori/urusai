"""StreamingDemuxer — single-ffmpeg HLS/DASH/progressive demux to mkdtemp.

Single-ffmpeg demux of HLS / DASH / progressive sources to mkdtemp.

Output layout:
  mkdtemp/
    audio.wav   16kHz mono PCM for ASR / diarization / audio_event / mss
    video.mp4   stream-copy for VLM clip extraction
    frames/     PySceneDetect-triggered keyframe dump for OCR

Source path policy: source_path field on EvidenceClaim always points to the
original URL or user-provided local path; mkdtemp is process-internal only.
"""
from __future__ import annotations

import asyncio
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Literal

Protocol = Literal["hls", "dash", "progressive", "file"]


def detect_protocol(source: str) -> Protocol:
    """Pick HLS / DASH / progressive / local-file from URL or path."""
    s = source.lower()
    if s.startswith("file://") or "://" not in s:
        return "file"
    if ".m3u8" in s:
        return "hls"
    if ".mpd" in s:
        return "dash"
    return "progressive"


class StreamingDemuxer:
    """Open a single ffmpeg subprocess, fan out to mkdtemp.

    Usage:
        async with StreamingDemuxer(url, ingest_id) as paths:
            ...
    """

    def __init__(self, source: str, ingest_id: str):
        self.source = source
        self.ingest_id = ingest_id
        self.protocol = detect_protocol(source)
        self._tmpdir: Path | None = None
        self._proc: asyncio.subprocess.Process | None = None

    @property
    def audio_wav(self) -> Path:
        assert self._tmpdir is not None
        return self._tmpdir / "audio.wav"

    @property
    def video_mp4(self) -> Path:
        assert self._tmpdir is not None
        return self._tmpdir / "video.mp4"

    @property
    def frames_dir(self) -> Path:
        assert self._tmpdir is not None
        return self._tmpdir / "frames"

    async def __aenter__(self) -> "StreamingDemuxer":
        self._tmpdir = Path(tempfile.mkdtemp(prefix=f"urusai_{self.ingest_id}_"))
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        # TODO: spawn ffmpeg with -i source -map 0:v -map 0:a -c copy
        # Audio path needs separate ffmpeg invocation to enforce 16kHz mono PCM.
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                await self._proc.wait()
            except ProcessLookupError:
                pass
        if self._tmpdir is not None and self._tmpdir.exists():
            shutil.rmtree(self._tmpdir, ignore_errors=True)


@asynccontextmanager
async def stream_video(source: str, ingest_id: str) -> AsyncIterator[StreamingDemuxer]:
    """Convenience wrapper for async with usage."""
    demuxer = StreamingDemuxer(source, ingest_id)
    async with demuxer:
        yield demuxer
