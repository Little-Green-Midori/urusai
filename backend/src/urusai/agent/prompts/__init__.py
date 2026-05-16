"""Prompt assets for urusai agents.

Each prompt is a standalone markdown file in this package directory. This
module loads them at import time and exposes constants + template helpers —
code never embeds prompt text inline.
"""
from __future__ import annotations

from pathlib import Path

from urusai.domain.evidence import EvidenceClaim
from urusai.domain.inventory import InventoryReport


_DIR = Path(__file__).parent


def _load(name: str) -> str:
    return (_DIR / name).read_text(encoding="utf-8")


INTEGRATOR_SYSTEM: str = _load("integrator_system.md")
CHAT_PERSONA: str = _load("chat_persona.md")
_INTEGRATOR_USER_TEMPLATE: str = _load("integrator_user.md")


def format_inventory_summary(inv: InventoryReport) -> str:
    a = inv.inventory
    return (
        f"- duration_sec: {a.duration_sec:.1f}\n"
        f"- has_audio: {a.has_audio}\n"
        f"- has_speech: {a.has_speech}\n"
        f"- has_music: {a.has_music}\n"
        f"- has_visual: {a.has_visual}\n"
        f"- visual_static: {a.visual_static}\n"
        f"- has_manual_subs: {a.has_manual_subs} (lang={a.subs_lang or '-'})"
    )


def format_evidence_block(claims: list[EvidenceClaim]) -> str:
    if not claims:
        return "(no evidence retrieved)"
    lines: list[str] = []
    for i, c in enumerate(claims):
        meta_parts: list[str] = []
        if c.confidence is not None:
            meta_parts.append(f"confidence={c.confidence.value}")
        if c.inference_strength is not None:
            meta_parts.append(f"inference={c.inference_strength.value}")
        meta = " ".join(meta_parts)
        line = (
            f"[{i}] channel={c.channel} "
            f"time={c.time_range.start:.2f}-{c.time_range.end:.2f}s "
            f"text={c.claim_text!r} "
            f"source={c.source_tool}"
        )
        if meta:
            line += f" {meta}"
        lines.append(line)
    return "\n".join(lines)


def integrator_user_prompt(
    query: str,
    inv: InventoryReport,
    evidence: list[EvidenceClaim],
    conflict_flags: list[str] | None = None,
) -> str:
    conflict_block = ""
    if conflict_flags:
        conflict_block = (
            "\n\nDetected same-layer conflicts (flag, not blocker):\n"
            + "\n".join(f"- {f}" for f in conflict_flags)
        )
    return _INTEGRATOR_USER_TEMPLATE.format(
        query=query,
        inventory_summary=format_inventory_summary(inv),
        evidence_block=format_evidence_block(evidence),
        conflict_block=conflict_block,
    )
