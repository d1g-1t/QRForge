from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis

from qrcode_service.config import Settings, get_settings
from qrcode_service.database import get_async_session_factory, get_db_session
from qrcode_service.generators.barcode_generator import BarcodeGenerator
from qrcode_service.generators.logo_embedder import LogoEmbedder
from qrcode_service.generators.qr_generator import QRGenerator
from qrcode_service.redis_client import get_redis, get_redis_binary
from qrcode_service.repositories.code_repo import CodeRepository
from qrcode_service.services.analytics_service import AnalyticsService
from qrcode_service.services.code_service import CodeService
from qrcode_service.services.scan_service import ScanService


def get_code_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CodeRepository:
    return CodeRepository(session)


def get_logo_embedder() -> LogoEmbedder:
    return LogoEmbedder()


def get_qr_generator(
    settings: Annotated[Settings, Depends(get_settings)],
    logo_embedder: Annotated[LogoEmbedder, Depends(get_logo_embedder)],
) -> QRGenerator:
    return QRGenerator(settings, logo_embedder)


def get_barcode_generator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> BarcodeGenerator:
    return BarcodeGenerator(settings)


async def get_code_service(
    settings: Annotated[Settings, Depends(get_settings)],
    code_repo: Annotated[CodeRepository, Depends(get_code_repo)],
    qr_generator: Annotated[QRGenerator, Depends(get_qr_generator)],
    barcode_generator: Annotated[BarcodeGenerator, Depends(get_barcode_generator)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    redis_binary: Annotated[redis.Redis, Depends(get_redis_binary)],
) -> CodeService:
    return CodeService(
        settings, code_repo, qr_generator, barcode_generator, redis_client, redis_binary
    )


async def get_scan_service(
    settings: Annotated[Settings, Depends(get_settings)],
    code_repo: Annotated[CodeRepository, Depends(get_code_repo)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> ScanService:
    return ScanService(settings, code_repo, redis_client)


async def get_analytics_service(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> AnalyticsService:
    return AnalyticsService(get_async_session_factory(), redis_client)


async def get_current_owner_id(
    x_owner_id: Annotated[str, Header()] = "00000000-0000-0000-0000-000000000000",
) -> uuid.UUID:
    return uuid.UUID(x_owner_id)
