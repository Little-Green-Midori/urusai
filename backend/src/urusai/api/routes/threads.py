"""Thread (agent session) endpoints under /v1/threads/.

thread_id is a string derived from session / ingest UUIDs.
State writes use deterministic keys so that interrupt + resume is idempotent.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/threads", tags=["threads"])


@router.post("")
async def create_thread() -> dict:
    """Body: ingest_id (or null for chat mode), provider_selection, title."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("")
async def list_threads(cursor: str | None = None, limit: int = 50) -> dict:
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/{thread_id}")
async def get_thread(thread_id: str) -> dict:
    raise HTTPException(status_code=501, detail="not implemented")


@router.patch("/{thread_id}")
async def patch_thread(thread_id: str) -> dict:
    """Change title / provider_selection."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str) -> dict:
    """Delete thread + all checkpoints."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str) -> dict:
    """Current AgentState snapshot."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/{thread_id}/checkpoints")
async def list_checkpoints(thread_id: str) -> dict:
    """Checkpoint history."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.post("/{thread_id}/checkpoints/{checkpoint_id}:fork")
async def fork_thread(thread_id: str, checkpoint_id: str) -> dict:
    """Fork a new thread from a specific checkpoint (exploration branch)."""
    raise HTTPException(status_code=501, detail="not implemented")
