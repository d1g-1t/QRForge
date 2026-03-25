from __future__ import annotations

from functools import lru_cache

import redis.asyncio as redis


@lru_cache
def _build_redis_client() -> redis.Redis:
    from qrcode_service.config import get_settings

    return redis.from_url(str(get_settings().REDIS_URL), decode_responses=True)


@lru_cache
def _build_redis_binary_client() -> redis.Redis:
    from qrcode_service.config import get_settings

    return redis.from_url(str(get_settings().REDIS_URL), decode_responses=False)


def get_redis_client() -> redis.Redis:
    return _build_redis_client()


def get_redis_binary_client() -> redis.Redis:
    return _build_redis_binary_client()


async def get_redis() -> redis.Redis:
    return get_redis_client()


async def get_redis_binary() -> redis.Redis:
    return get_redis_binary_client()
