"""Inventory probe — cheap pre-pass during ingest.

Decides which channels can contribute evidence for the current video and
hands that decision to the channel dispatcher. Requires `ffmpeg`,
`ffprobe`, and `yt-dlp` on the system PATH.

Dispatcher keys are channel concept names (`asr`, `subtitle`, `scene`),
matching the channel slot keys registered in `ChannelRegistry`.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from urusai.domain.inventory import ChannelAvailability, InventoryReport


VOICE_BAND_HZ = (300, 3400)
VOICE_BAND_RATIO_SPEECH = 0.30
VOICE_BAND_RATIO_MUSIC = 0.21
RMS_SILENCE_THRESHOLD = 0.001
BLACK_FRAME_RATIO_THRESHOLD = 0.85
PROBE_AUDIO_DURATION_SEC = 30.0


def ffprobe_metadata(source_path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", source_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return {"streams": [], "format": {}}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"streams": [], "format": {}}


def extract_audio_sample(
    source_path: str, duration_sec: float = PROBE_AUDIO_DURATION_SEC
) -> tuple[np.ndarray, int] | None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        cmd = [
            "ffmpeg", "-y", "-loglevel", "quiet",
            "-i", source_path,
            "-t", str(duration_sec),
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            wav_path,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode != 0:
            return None
        data, sr = sf.read(wav_path)
        if data.ndim > 1:
            data = data.mean(axis=1)
        return data.astype(np.float32), int(sr)
    except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError):
        return None
    finally:
        Path(wav_path).unlink(missing_ok=True)


def voice_band_ratio(samples: np.ndarray, sr: int) -> float:
    if samples.size < sr:
        return 0.0
    fft = np.abs(np.fft.rfft(samples))
    freqs = np.fft.rfftfreq(samples.size, 1.0 / sr)
    voice_mask = (freqs >= VOICE_BAND_HZ[0]) & (freqs <= VOICE_BAND_HZ[1])
    voice_energy = float((fft[voice_mask] ** 2).sum())
    total_energy = float((fft ** 2).sum())
    if total_energy <= 0.0:
        return 0.0
    return voice_energy / total_energy


def rms(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))


def probe_video_blackdetect(
    source_path: str, sample_duration_sec: float = 30.0
) -> float:
    cmd = [
        "ffmpeg", "-loglevel", "info", "-t", str(sample_duration_sec),
        "-i", source_path, "-vf", "blackdetect=d=0.05:pix_th=0.10",
        "-an", "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return 0.0
    total_black = 0.0
    for line in result.stderr.splitlines():
        if "blackdetect" in line and "black_duration" in line:
            for token in line.split():
                if token.startswith("black_duration:"):
                    try:
                        total_black += float(token.split(":", 1)[1])
                    except ValueError:
                        pass
    return min(1.0, total_black / sample_duration_sec)


def probe_subtitles(url: str | None) -> tuple[bool, str | None]:
    if not url:
        return False, None
    try:
        cmd = [
            "yt-dlp", "--list-subs", "--skip-download",
            "--no-warnings", url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, None
    out = result.stdout
    if "Available subtitles" not in out:
        return False, None
    manual_section = out.split("Available subtitles", 1)[1]
    if "Available automatic captions" in manual_section:
        manual_section = manual_section.split("Available automatic captions", 1)[0]
    for line in manual_section.splitlines():
        s = line.strip()
        if not s or s.lower().startswith("language") or s.startswith("[") or "subtitle" in s.lower():
            continue
        parts = s.split()
        if parts and len(parts[0]) <= 8:
            return True, parts[0]
    return False, None


def run_inventory_probe(
    source_path: str,
    video_id: str,
    url: str | None = None,
) -> InventoryReport:
    """Cheap probe that builds an `InventoryReport` describing which channels should run."""
    meta = ffprobe_metadata(source_path)
    streams = meta.get("streams", [])
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video_streams = [s for s in streams if s.get("codec_type") == "video"]

    try:
        duration_sec = float(meta.get("format", {}).get("duration", 0.0))
    except (TypeError, ValueError):
        duration_sec = 0.0

    has_audio = len(audio_streams) > 0
    has_visual = len(video_streams) > 0

    has_speech = False
    has_music = False
    if has_audio:
        sample = extract_audio_sample(source_path)
        if sample is not None:
            samples, sr = sample
            if rms(samples) > RMS_SILENCE_THRESHOLD:
                vb = voice_band_ratio(samples, sr)
                has_speech = vb > VOICE_BAND_RATIO_SPEECH
                has_music = vb < VOICE_BAND_RATIO_MUSIC

    visual_static = False
    if has_visual:
        black_ratio = probe_video_blackdetect(source_path)
        visual_static = black_ratio > BLACK_FRAME_RATIO_THRESHOLD

    has_manual_subs, subs_lang = probe_subtitles(url)

    inv = ChannelAvailability(
        has_audio=has_audio,
        has_speech=has_speech,
        has_music=has_music,
        has_visual=has_visual,
        visual_static=visual_static,
        has_manual_subs=has_manual_subs,
        subs_lang=subs_lang,
        duration_sec=duration_sec,
    )

    dispatched: list[str] = []
    skipped: dict[str, str] = {}

    if has_speech and has_manual_subs:
        dispatched.append("subtitle")
    elif has_speech:
        dispatched.append("asr")
    else:
        skipped["asr"] = "no speech detected"
        skipped["subtitle"] = "no speech to subtitle"

    if has_visual and not visual_static:
        dispatched.append("scene")
    elif not has_visual:
        skipped["scene"] = "no video stream"
    else:
        skipped["scene"] = "visual is static / mostly black"

    return InventoryReport(
        video_id=video_id,
        source_path=source_path,
        inventory=inv,
        dispatched_channels=dispatched,
        skipped_channels=skipped,
    )
