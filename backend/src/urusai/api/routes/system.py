"""Diagnostics endpoints under /v1/system/."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/providers")
async def list_providers() -> dict:
    """Registered providers per channel + their capabilities + config_class."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("/limits")
async def get_limits() -> dict:
    """TokenRotator per-key cooldown + quota estimates + Gemini RPD/RPM snapshot."""
    raise HTTPException(status_code=501, detail="not implemented")
