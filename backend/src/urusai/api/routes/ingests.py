"""Ingest resource endpoints — POST/GET/DELETE /v1/ingests + :batch + :rechannel.

Ingest endpoints. Long operations return 202 + Location pointing at /v1/jobs/<id>.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/v1/ingests", tags=["ingests"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_ingest() -> dict:
    """Create ingest job. Returns 202 + Location: /v1/jobs/{job_id}."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.post(":batch", status_code=status.HTTP_202_ACCEPTED)
async def create_ingest_batch() -> dict:
    """Multi-file batch ingest job. Returns 202 + Location."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("")
async def list_ingests(cursor: str | None = None, limit: int = 50) -> dict:
    """List ingests with cursor pagination."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/{ingest_id}")
async def get_ingest(ingest_id: str) -> dict:
    """Detail: inventory + counts + thread refs."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.delete("/{ingest_id}")
async def delete_ingest(ingest_id: str) -> dict:
    """CASCADE delete evidence + Milvus collection; orphan threads marked."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.post("/{ingest_id}:rechannel", status_code=status.HTTP_202_ACCEPTED)
async def rechannel_ingest(ingest_id: str) -> dict:
    """Add new channel(s) to existing ingest; async job."""
    raise HTTPException(status_code=501, detail="not implemented")
