"""Evidence trace serialization。"""
from __future__ import annotations

from urusai.agent.state import AgentState
from urusai.domain.evidence import EvidenceClaim


def serialize_trace(
    claims: list[EvidenceClaim],
    cited_indices: list[int] | None = None,
) -> str:
    """Format cited evidence as human-readable trace。

    `cited_indices=None` 時、序列化全部；否則只序列化指定 indices。
    """
    if not claims:
        return "(no evidence)"
    if cited_indices is None:
        indices = list(range(len(claims)))
    else:
        indices = cited_indices

    lines: list[str] = []
    for i in indices:
        if not (0 <= i < len(claims)):
            continue
        c = claims[i]
        lines.append(
            f"[{i}] {c.channel} {c.time_range.start:.2f}-{c.time_range.end:.2f}s "
            f"{c.claim_text!r} (source: {c.source_tool})"
        )
    return "\n".join(lines) if lines else "(empty trace)"


def has_complete_trace(state: AgentState) -> bool:
    """final answer 必須帶非空 cited_indices 才算 trace 完整。"""
    return state.final_answer is not None and bool(state.cited_indices)
