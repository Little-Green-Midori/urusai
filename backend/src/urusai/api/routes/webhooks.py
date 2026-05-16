"""Webhook registration endpoints under /v1/webhooks.

Payload defaults to metadata-only; include_sensitive_payload
requires explicit opt-in + trifecta lint check.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


@router.post("")
async def register_webhook() -> dict:
    """Body: url, event_types, secret (for HMAC-SHA256 sign)."""
    raise HTTPException(status_code=501, detail="not implemented")


@router.get("")
async def list_webhooks() -> dict:
    raise HTTPException(status_code=501, detail="not implemented")


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str) -> dict:
    raise HTTPException(status_code=501, detail="not implemented")
