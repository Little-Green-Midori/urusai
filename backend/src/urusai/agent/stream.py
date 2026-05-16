"""Data Stream Protocol encoder + run_events idempotent write helpers.

SSE Data Stream Protocol encoder: deterministic event_id + heartbeat.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


HEARTBEAT_INTERVAL_SEC = 15.0


def make_event_id(run_id: str, node_name: str, interrupt_aware_seq: int, chunk_seq: int) -> str:
    """Deterministic event_id per H4. Identical across resume so ON CONFLICT DO NOTHING dedups."""
    return f"{node_name}:{interrupt_aware_seq}:{chunk_seq}"


def encode_sse_event(
    event_type: str,
    data: dict[str, Any] | str,
    event_id: str | None = None,
) -> str:
    """Format one SSE event line."""
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if isinstance(data, str):
        payload = data
    else:
        payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    lines.append(f"data: {payload}")
    return "\n".join(lines) + "\n\n"


def heartbeat() -> str:
    """One heartbeat event (not written to run_events; pure keep-alive)."""
    return encode_sse_event("heartbeat", {})


def done() -> str:
    """Stream terminator."""
    return "data: [DONE]\n\n"


@dataclass
class HeartbeatTicker:
    """Tracks when to emit a heartbeat alongside the real event stream."""

    interval_sec: float = HEARTBEAT_INTERVAL_SEC
    _last: float = field(default_factory=time.monotonic)

    def due(self) -> bool:
        return time.monotonic() - self._last >= self.interval_sec

    def reset(self) -> None:
        self._last = time.monotonic()


UPSERT_RUN_EVENT_SQL = """
INSERT INTO run_events (run_id, event_id, event_payload)
VALUES (:run_id, :event_id, :event_payload)
ON CONFLICT (run_id, event_id) DO NOTHING
"""

UPSERT_JOB_EVENT_SQL = """
INSERT INTO job_events (job_id, event_id, event_payload)
VALUES (:job_id, :event_id, :event_payload)
ON CONFLICT (job_id, event_id) DO NOTHING
"""

REPLAY_RUN_EVENTS_SINCE_SQL = """
SELECT event_id, event_payload
  FROM run_events
 WHERE run_id = :run_id
   AND event_id > :last_event_id
 ORDER BY created_at ASC
"""

REPLAY_JOB_EVENTS_SINCE_SQL = """
SELECT event_id, event_payload
  FROM job_events
 WHERE job_id = :job_id
   AND event_id > :last_event_id
 ORDER BY created_at ASC
"""
