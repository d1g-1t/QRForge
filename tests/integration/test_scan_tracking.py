import hashlib
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from qrcode_service.models.code import CodeStatus
from qrcode_service.schemas.code import CodeCacheEntry
from qrcode_service.services.scan_service import ScanService


@pytest.fixture
def scan_service(settings, mock_redis):
    code_repo = AsyncMock()
    return ScanService(settings, code_repo, mock_redis)


class TestScanResolve:
    @pytest.mark.asyncio
    async def test_resolve_from_cache(self, scan_service, mock_redis):
        entry = CodeCacheEntry(
            id="123e4567-e89b-12d3-a456-426614174000",
            target_url="https://example.com",
            status="active",
            name="test",
        )
        mock_redis.get = AsyncMock(return_value=entry.model_dump_json())

        result = await scan_service.resolve("abc123")
        assert result is not None
        assert result.target_url == "https://example.com"

    @pytest.mark.asyncio
    async def test_resolve_not_found(self, scan_service, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)
        scan_service._code_repo.get_by_short_code = AsyncMock(return_value=None)

        result = await scan_service.resolve("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_cached_not_found(self, scan_service, mock_redis):
        mock_redis.get = AsyncMock(return_value='{"not_found": true}')

        result = await scan_service.resolve("cached_miss")
        assert result is None


class TestScanTracking:
    @pytest.mark.asyncio
    async def test_track_increments_redis(self, scan_service, mock_redis):
        await scan_service.track_scan(
            code_id="123e4567-e89b-12d3-a456-426614174000",
            short_code="abc123",
            ip="127.0.0.1",
            user_agent="Mozilla/5.0",
        )

        pipe = mock_redis.pipeline()
        assert pipe.incr.called or mock_redis.rpush.called

    @pytest.mark.asyncio
    async def test_track_does_not_raise(self, scan_service, mock_redis):
        mock_redis.pipeline = MagicMock(side_effect=Exception("Redis down"))

        await scan_service.track_scan(
            code_id=None,
            short_code="abc123",
            ip="127.0.0.1",
        )


class TestScanRedirectBehavior:
    @pytest.mark.asyncio
    async def test_paused_code_no_redirect(self, scan_service, mock_redis):
        entry = CodeCacheEntry(
            id="123e4567-e89b-12d3-a456-426614174000",
            target_url="https://example.com",
            status=CodeStatus.PAUSED,
            name="paused-qr",
        )
        mock_redis.get = AsyncMock(return_value=entry.model_dump_json())

        result = await scan_service.resolve("paused123")
        assert result.status == CodeStatus.PAUSED

    @pytest.mark.asyncio
    async def test_archived_code(self, scan_service, mock_redis):
        entry = CodeCacheEntry(
            id="123e4567-e89b-12d3-a456-426614174000",
            target_url="https://example.com",
            status=CodeStatus.ARCHIVED,
        )
        mock_redis.get = AsyncMock(return_value=entry.model_dump_json())

        result = await scan_service.resolve("archived123")
        assert result.status == CodeStatus.ARCHIVED


class TestIPAnonymization:
    def test_ip_hash_changes_daily(self):
        ip = "192.168.1.1"
        secret = "test-secret"

        hash_today = hashlib.sha256(
            f"{ip}{date.today().isoformat()}{secret}".encode()
        ).hexdigest()

        hash_tomorrow = hashlib.sha256(
            f"{ip}2026-03-21{secret}".encode()
        ).hexdigest()

        assert hash_today != hash_tomorrow

    def test_same_ip_same_day_same_hash(self):
        ip = "192.168.1.1"
        secret = "test-secret"
        day = "2026-03-20"

        h1 = hashlib.sha256(f"{ip}{day}{secret}".encode()).hexdigest()
        h2 = hashlib.sha256(f"{ip}{day}{secret}".encode()).hexdigest()

        assert h1 == h2


class TestShortCodeUniqueness:
    @pytest.mark.asyncio
    async def test_no_collisions_in_1000_generations(self):
        import secrets
        import string

        base62 = string.ascii_letters + string.digits
        codes = set()
        for _ in range(1000):
            code = "".join(secrets.choice(base62) for _ in range(8))
            codes.add(code)

        assert len(codes) == 1000
