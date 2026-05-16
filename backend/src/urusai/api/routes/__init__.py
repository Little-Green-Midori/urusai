"""URUSAI API routes — split per resource.

Mounted by urusai.api.main:create_app. Each module exports `router: APIRouter`.
"""
from urusai.api.routes import (
    healthz,
    ingests,
    interrupts,
    jobs,
    runs,
    system,
    threads,
    webhooks,
)

__all__ = [
    "healthz",
    "ingests",
    "jobs",
    "threads",
    "runs",
    "interrupts",
    "webhooks",
    "system",
]
