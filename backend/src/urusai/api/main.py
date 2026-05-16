"""FastAPI app entry — mounts /v1/ routes + lifespan-managed checkpointer.

FastAPI app factory + lifespan + router mount.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from urusai import __version__
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
from urusai.db.session import dispose_engine


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: future home of LangGraph build_graph + token rotator init.

    Shutdown: close SQLAlchemy engine.
    """
    # TODO: lifespan startup
    # - build_graph(settings.langgraph_postgres_dsn) -> app.state.graph
    # - construct TokenRotator instances per provider family -> app.state.rotators
    # - milvus client connection pool -> app.state.milvus
    try:
        yield
    finally:
        await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="urusai", version=__version__, lifespan=_lifespan)

    # No-prefix liveness/readiness.
    app.include_router(healthz.router)

    # /v1/ business endpoints.
    app.include_router(ingests.router)
    app.include_router(jobs.router)
    app.include_router(threads.router)
    app.include_router(runs.router)
    app.include_router(interrupts.router)
    app.include_router(webhooks.router)
    app.include_router(system.router)

    return app


app = create_app()
