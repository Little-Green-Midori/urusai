"""Prompt templates —— Phase 1 integrator prompt + evidence formatting helpers."""
from __future__ import annotations

from urusai.domain.evidence import EvidenceClaim
from urusai.domain.inventory import InventoryReport


INTEGRATOR_SYSTEM = """You are urusai, an agent that answers questions about videos using ONLY the retrieved evidence from structured notebooks.

Strict rules:
1. Every factual claim in your answer MUST cite specific evidence by its index, with the timestamp.
2. If retrieved evidence is INSUFFICIENT to answer, you MUST abstain.
3. Never fabricate information not in the evidence.
4. Keep answers concise and grounded.
5. Use the same language the query is written in for your answer.

Output ONLY valid JSON in this exact schema (no markdown fences, no extra text):
{
  "status": "answered" | "abstain",
  "answer": "<grounded answer string with inline timestamps>" | null,
  "cited_evidence_indices": [<list of int indices into the evidence list>],
  "abstain_kind": "evidence_insufficient" | null,
  "abstain_reason": "<short reason in user's language>" | null
}

When answered:
- answer is non-null
- cited_evidence_indices must be non-empty

When abstain:
- answer is null
- cited_evidence_indices is []
- abstain_kind = "evidence_insufficient"
- abstain_reason explains what's missing"""


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
        lines.append(
            f"[{i}] channel={c.channel} "
            f"time={c.time_range.start:.2f}-{c.time_range.end:.2f}s "
            f"text={c.claim_text!r} "
            f"source={c.source_tool}"
        )
    return "\n".join(lines)


def integrator_user_prompt(
    query: str,
    inv: InventoryReport,
    evidence: list[EvidenceClaim],
) -> str:
    return f"""Query: {query}

Video inventory:
{format_inventory_summary(inv)}

Retrieved evidence (each line is one observation):
{format_evidence_block(evidence)}

Answer the query strictly from the evidence above. Cite indices for every claim. If evidence does not contain the answer, abstain."""
