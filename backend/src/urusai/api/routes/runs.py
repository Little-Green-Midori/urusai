"""Run endpoints under /v1/threads/{id}/runs/.

SSE events use deterministic event_id + a periodic heartbeat for client resume.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/v1/threads/{thread_id}/runs", tags=["runs"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_run(thread_id: str) -> dict:
    """Body: message or query + optional per-run provider_overrides.

    Returns 202 + Location: /v1/threads/{thread_id}/runs/{run_id}.
    """
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("")
async def list_runs(thread_id: str) -> dict:
    """Historical runs in this thread."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/{run_id}")
async def get_run(thread_id: str, run_id: str) -> dict:
    """Run status + final answer + cited evidence."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/{run_id}/events")
async def stream_run_events(thread_id: str, run_id: str):
    """SSE Data Stream Protocol stream.

    Header: x-vercel-ai-ui-message-stream: v1
    Resumable via Last-Event-ID.
    Heartbeat every 15s.
    """
    raise HTTPException(status_code=501, detail="not implemented")


@router.post("/{run_id}:cancel")
async def cancel_run(thread_id: str, run_id: str) -> dict:
    raise HTTPException(status_code=501, detail="not implemented")
