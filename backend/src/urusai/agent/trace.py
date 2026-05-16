"""Evidence trace serialization."""
from __future__ import annotations

from urusai.agent.state import AgentState
from urusai.domain.evidence import EvidenceClaim


def serialize_trace(
    claims: list[EvidenceClaim],
    cited_indices: list[int] | None = None,
) -> str:
    """Format cited evidence as a human-readable trace.

    When `cited_indices` is None, every claim is serialised. Otherwise only
    the indices listed are serialised.
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
    """A trace is complete only when the final answer carries a non-empty cited_indices list."""
    return state.final_answer is not None and bool(state.cited_indices)
