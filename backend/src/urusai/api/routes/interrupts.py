"""HITL interrupt endpoints under /v1/threads/{id}/interrupts/.

interrupt() pauses graph; client lists pending and resumes via Command(resume=...).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/threads/{thread_id}/interrupts", tags=["hitl"])


@router.get("")
async def list_interrupts(thread_id: str) -> dict:
    """List pending interrupts: [{interrupt_id, payload, node, ts}, ...]."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.post("/{interrupt_id}:resume")
async def resume_interrupt(thread_id: str, interrupt_id: str) -> dict:
    """Send Command(resume=value); graph re-executes the interrupted node."""
    raise HTTPException(status_code=501, detail="not implemented")
