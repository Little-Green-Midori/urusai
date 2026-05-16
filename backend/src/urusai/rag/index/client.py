"""MilvusClient wrapper with connection (singleton-ish).

Milvus client wrapper with pool-aware lifecycle.
"""
from __future__ import annotations

from functools import lru_cache

from urusai.config.settings import get_settings


@lru_cache(maxsize=1)
def get_milvus_client():
    """Return a configured pymilvus.MilvusClient."""
    from pymilvus import MilvusClient  # lazy import to avoid module-load cost

    settings = get_settings()
    return MilvusClient(
        uri=settings.milvus_uri,
        token=settings.milvus_token or None,
    )
