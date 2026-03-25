import pytest
from io import BytesIO

from PIL import Image

from qrcode_service.generators.qr_generator import QRGenerator
from qrcode_service.generators.logo_embedder import LogoEmbedder
from qrcode_service.schemas.code import QRGenerationConfig


@pytest.fixture
def logo_embedder():
    return LogoEmbedder()


@pytest.fixture
def qr_generator(settings, logo_embedder):
    return QRGenerator(settings, logo_embedder)


class TestQRGeneratorPNG:
    @pytest.mark.asyncio
    async def test_generates_valid_png(self, qr_generator):
        config = QRGenerationConfig(content="https://example.com", output_format="png")
        result = await qr_generator.generate(config)

        assert result.content_type == "image/png"
        assert result.size_bytes > 0
        assert result.data[:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_png_dimensions(self, qr_generator):
        config = QRGenerationConfig(content="test", output_format="png", scale=10, border=4)
        result = await qr_generator.generate(config)

        img = Image.open(BytesIO(result.data))
        assert img.width > 0
        assert img.height > 0
        assert result.width == img.width
        assert result.height == img.height


class TestQRGeneratorSVG:
    @pytest.mark.asyncio
    async def test_generates_valid_svg(self, qr_generator):
        config = QRGenerationConfig(content="https://example.com", output_format="svg")
        result = await qr_generator.generate(config)

        assert result.content_type == "image/svg+xml"
        svg_str = result.data.decode("utf-8")
        assert "<svg" in svg_str
        assert "</svg>" in svg_str

    @pytest.mark.asyncio
    async def test_svg_has_valid_xml(self, qr_generator):
        config = QRGenerationConfig(content="test data", output_format="svg")
        result = await qr_generator.generate(config)

        import xml.etree.ElementTree as ET
        ET.fromstring(result.data)


class TestQRGeneratorWebP:
    @pytest.mark.asyncio
    async def test_generates_webp(self, qr_generator):
        config = QRGenerationConfig(content="https://example.com", output_format="webp")
        result = await qr_generator.generate(config)

        assert result.content_type == "image/webp"
        assert result.size_bytes > 0

    @pytest.mark.asyncio
    async def test_webp_smaller_than_png_for_large_content(self, qr_generator):
        content = "https://example.com/" + "a" * 200
        png_config = QRGenerationConfig(content=content, output_format="png", scale=20)
        webp_config = QRGenerationConfig(content=content, output_format="webp", scale=20)

        png_result = await qr_generator.generate(png_config)
        webp_result = await qr_generator.generate(webp_config)

        assert webp_result.size_bytes < png_result.size_bytes


class TestQRGeneratorWithLogo:
    @pytest.mark.asyncio
    async def test_png_with_logo(self, qr_generator, logo_bytes):
        config = QRGenerationConfig(
            content="https://example.com",
            output_format="png",
            error_correction="H",
            logo_size_ratio=0.25,
        )
        result = await qr_generator.generate(config, logo=logo_bytes)

        assert result.content_type == "image/png"
        assert result.size_bytes > 0

    @pytest.mark.asyncio
    async def test_svg_with_logo(self, qr_generator, logo_bytes):
        config = QRGenerationConfig(
            content="https://example.com",
            output_format="svg",
            error_correction="H",
            logo_size_ratio=0.25,
        )
        result = await qr_generator.generate(config, logo=logo_bytes)

        svg_str = result.data.decode("utf-8")
        assert "base64" in svg_str
        assert "href" in svg_str


class TestQRGeneratorErrorCorrection:
    @pytest.mark.asyncio
    async def test_error_correction_h(self, qr_generator):
        config = QRGenerationConfig(
            content="test", error_correction="H", output_format="png"
        )
        result = await qr_generator.generate(config)
        assert result.error_correction == "H"

    @pytest.mark.asyncio
    async def test_error_correction_l(self, qr_generator):
        config = QRGenerationConfig(
            content="test", error_correction="L", output_format="png"
        )
        result = await qr_generator.generate(config)
        assert result.error_correction is not None
