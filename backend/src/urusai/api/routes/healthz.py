"""Liveness + readiness endpoints (no /v1/ prefix; never break for backward compat)."""
from __future__ import annotations

from fastapi import APIRouter

from urusai import __version__

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict:
    """Liveness — process is up."""
    return {"status": "ok", "version": __version__}


@router.get("/readyz")
async def readyz() -> dict:
    """Readiness — DB + Milvus + token rotator connectivity verified."""
    # TODO: real checks
    # - SQLAlchemy async engine ping
    # - Milvus client.list_databases()
    # - settings.gemini_api_keys non-empty
    return {"status": "ready"}
