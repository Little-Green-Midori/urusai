"""FastAPI app entry。"""
from fastapi import FastAPI

from urusai import __version__
from urusai.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="urusai", version=__version__)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok", "version": __version__}

    app.include_router(router)
    return app


app = create_app()
