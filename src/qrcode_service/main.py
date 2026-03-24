from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from qrcode_service.config import get_settings
from qrcode_service.api.v1.router import router
from qrcode_service.database import get_engine
from qrcode_service.middleware import TimingMiddleware
from qrcode_service.redis_client import get_redis_client


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await get_redis_client().aclose()
    await get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="QR + barcode generation with custom logo, scan tracking, and analytics.",
        lifespan=lifespan,
    )

    application.add_middleware(TimingMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(router)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
