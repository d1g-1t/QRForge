from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock()
    r.delete = AsyncMock()
    r.incr = AsyncMock()
    r.expire = AsyncMock()
    r.rpush = AsyncMock()
    pipe = AsyncMock()
    pipe.incr = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock()
    r.pipeline = MagicMock(return_value=pipe)
    return r


@pytest.fixture
def mock_redis_binary():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock()
    return r


@pytest.fixture
def settings():
    from qrcode_service.config import Settings

    return Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/qrforge_test",
        REDIS_URL="redis://localhost:6379/1",
        IP_HASH_SECRET="test-secret",
        BASE_URL="https://test.example.com",
    )


@pytest.fixture
def logo_bytes():
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    from unittest.mock import patch

    mock_settings_obj = MagicMock()
    mock_settings_obj.APP_NAME = "QRForge"
    mock_settings_obj.DEBUG = False
    mock_settings_obj.DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/qrforge_test"
    mock_settings_obj.REDIS_URL = "redis://localhost:6379/1"
    mock_settings_obj.BASE_URL = "https://test.example.com"
    mock_settings_obj.GENERATION_WORKERS = 2
    mock_settings_obj.GENERATION_CACHE_TTL_SECONDS = 60
    mock_settings_obj.MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024
    mock_settings_obj.SHORT_CODE_LENGTH = 8
    mock_settings_obj.IP_HASH_SECRET = MagicMock()
    mock_settings_obj.IP_HASH_SECRET.get_secret_value.return_value = "test"
    mock_settings_obj.GEOIP_DATABASE_PATH = "/tmp/geo.mmdb"
    mock_settings_obj.SCAN_CACHE_TTL_SECONDS = 300

    with patch("qrcode_service.config.get_settings", return_value=mock_settings_obj):
        with patch("qrcode_service.database._settings", mock_settings_obj):
            pass

    yield AsyncClient(base_url="https://test.example.com")
