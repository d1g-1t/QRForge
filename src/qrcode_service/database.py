from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


@lru_cache
def _get_engine() -> AsyncEngine:
    from qrcode_service.config import get_settings

    settings = get_settings()
    return create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=10,
    )


@lru_cache
def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_get_engine(), expire_on_commit=False)


def get_engine() -> AsyncEngine:
    return _get_engine()


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    return _get_session_factory()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_async_session_factory()
    async with factory() as session:
        yield session
