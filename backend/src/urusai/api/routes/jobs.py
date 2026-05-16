"""Job lifecycle endpoints — GET /v1/jobs/{id} + /events + :cancel.

Job endpoints. Long ops emit SSE via the job_events table
with deterministic event_id + ON CONFLICT for idempotency.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    """Job status: queued / running / succeeded / failed / canceled."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str):
    """SSE stream of per-channel progress; resumable via Last-Event-ID."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.post("/{job_id}:cancel")
async def cancel_job(job_id: str) -> dict:
    """Best-effort cancel; channels in-flight preserve partial evidence."""
    raise HTTPException(status_code=501, detail="not implemented")
