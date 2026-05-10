"""對白本 channel from manual subtitles —— yt-dlp 抓 + pysrt/webvtt 解析。

只接 manual subs（不抓 auto-generated、那是別人 ASR）。
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pysrt
import webvtt

from urusai.domain.evidence import ConfidenceMarker, EvidenceClaim, TimeRange


def _srt_time_to_seconds(t: pysrt.SubRipTime) -> float:
    return t.hours * 3600 + t.minutes * 60 + t.seconds + t.milliseconds / 1000.0


def _vtt_time_to_seconds(t: str) -> float:
    parts = t.split(":")
    if len(parts) == 3:
        h_part, m_part, rest = parts
    elif len(parts) == 2:
        h_part, m_part, rest = "0", parts[0], parts[1]
    else:
        return 0.0
    s_part, _, ms_part = rest.partition(".")
    try:
        h = int(h_part)
        m = int(m_part)
        s = int(s_part)
        ms = int(ms_part) if ms_part else 0
    except ValueError:
        return 0.0
    return h * 3600 + m * 60 + s + ms / 1000.0


def parse_srt(srt_path: str, lang: str) -> list[EvidenceClaim]:
    items = pysrt.open(srt_path)
    claims: list[EvidenceClaim] = []
    for sub in items:
        start = _srt_time_to_seconds(sub.start)
        end = _srt_time_to_seconds(sub.end)
        text = sub.text.strip()
        if not text or end <= start:
            continue
        claims.append(
            EvidenceClaim(
                channel="dialogue",
                time_range=TimeRange(start=start, end=end),
                claim_text=text,
                raw_quote=text,
                confidence=ConfidenceMarker.CLEAR,
                source_tool=f"manual_subs_{lang}",
            )
        )
    return claims


def parse_vtt(vtt_path: str, lang: str) -> list[EvidenceClaim]:
    claims: list[EvidenceClaim] = []
    for caption in webvtt.read(vtt_path):
        start = _vtt_time_to_seconds(caption.start)
        end = _vtt_time_to_seconds(caption.end)
        text = caption.text.strip()
        if not text or end <= start:
            continue
        claims.append(
            EvidenceClaim(
                channel="dialogue",
                time_range=TimeRange(start=start, end=end),
                claim_text=text,
                raw_quote=text,
                confidence=ConfidenceMarker.CLEAR,
                source_tool=f"manual_subs_{lang}",
            )
        )
    return claims


def fetch_manual_subs(
    url: str, lang: str, out_dir: str | None = None
) -> str | None:
    if out_dir is None:
        out_dir = tempfile.mkdtemp(prefix="urusai_subs_")
    out_template = str(Path(out_dir) / "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp", "--write-subs", "--skip-download",
        "--sub-langs", lang,
        "--sub-format", "srt/vtt/best",
        "--no-warnings", "-o", out_template, url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    for ext in (".srt", ".vtt"):
        matches = list(Path(out_dir).glob(f"*{ext}"))
        if matches:
            return str(matches[0])
    return None


class SubtitleChannel:
    """對白本 from manual subtitle file or URL（via yt-dlp）。"""

    name = "dialogue"

    async def extract_from_file(
        self, sub_path: str, lang: str = "und"
    ) -> list[EvidenceClaim]:
        if sub_path.endswith(".srt"):
            return parse_srt(sub_path, lang)
        if sub_path.endswith(".vtt"):
            return parse_vtt(sub_path, lang)
        raise ValueError(f"Unsupported subtitle format: {sub_path}")

    async def extract_from_url(
        self, url: str, lang: str
    ) -> list[EvidenceClaim]:
        sub_path = fetch_manual_subs(url, lang)
        if sub_path is None:
            return []
        return await self.extract_from_file(sub_path, lang)
