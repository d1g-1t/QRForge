import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qrcode_service.generators.barcode_generator import BarcodeGenerator
from qrcode_service.generators.logo_embedder import LogoEmbedder
from qrcode_service.generators.qr_generator import QRGenerator
from qrcode_service.schemas.code import QRGenerationConfig, BarcodeGenerationConfig, CodeCreate
from qrcode_service.services.code_service import CodeService


@pytest.fixture
def code_service(settings, mock_redis, mock_redis_binary):
    logo_embedder = LogoEmbedder()
    qr_gen = QRGenerator(settings, logo_embedder)
    bc_gen = BarcodeGenerator(settings)
    code_repo = AsyncMock()
    code_repo.short_code_exists = AsyncMock(return_value=False)
    code_repo.create = AsyncMock(side_effect=lambda c: c)
    return CodeService(settings, code_repo, qr_gen, bc_gen, mock_redis, mock_redis_binary)


class TestGenerateQREndpoint:
    @pytest.mark.asyncio
    async def test_generate_qr_png(self, code_service):
        config = QRGenerationConfig(content="https://example.com")
        result = await code_service.generate_qr_image(config)
        assert result.content_type == "image/png"
        assert result.data[:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_generate_qr_svg(self, code_service):
        config = QRGenerationConfig(content="https://example.com", output_format="svg")
        result = await code_service.generate_qr_image(config)
        assert result.content_type == "image/svg+xml"
        assert b"<svg" in result.data

    @pytest.mark.asyncio
    async def test_generate_qr_webp(self, code_service):
        config = QRGenerationConfig(content="https://example.com", output_format="webp")
        result = await code_service.generate_qr_image(config)
        assert result.content_type == "image/webp"

    @pytest.mark.asyncio
    async def test_generate_qr_with_logo(self, code_service, logo_bytes):
        config = QRGenerationConfig(
            content="https://example.com",
            error_correction="H",
            logo_size_ratio=0.25,
        )
        result = await code_service.generate_qr_image(config, logo=logo_bytes)
        assert result.content_type == "image/png"
        assert result.size_bytes > 0


class TestGenerateBarcodeEndpoint:
    @pytest.mark.asyncio
    async def test_generate_barcode(self, code_service):
        config = BarcodeGenerationConfig(
            barcode_type="code128", value="TEST-123"
        )
        result = await code_service.generate_barcode_image(config)
        assert result.content_type == "image/png"


class TestGenerationCache:
    @pytest.mark.asyncio
    async def test_same_config_uses_cache(self, code_service, mock_redis_binary):
        config = QRGenerationConfig(content="https://cache-test.com")

        result1 = await code_service.generate_qr_image(config)
        assert mock_redis_binary.setex.called

        mock_redis_binary.get = AsyncMock(return_value=result1.data)

        result2 = await code_service.generate_qr_image(config)
        assert result2.data == result1.data
