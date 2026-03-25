import pytest

from qrcode_service.generators.barcode_generator import BarcodeGenerator
from qrcode_service.schemas.code import BarcodeGenerationConfig


@pytest.fixture
def barcode_generator(settings):
    return BarcodeGenerator(settings)


class TestBarcodeGeneratorCode128:
    @pytest.mark.asyncio
    async def test_generates_code128_png(self, barcode_generator):
        config = BarcodeGenerationConfig(
            barcode_type="code128",
            value="ABC-12345",
            output_format="png",
        )
        result = await barcode_generator.generate(config)
        assert result.content_type == "image/png"
        assert result.size_bytes > 0

    @pytest.mark.asyncio
    async def test_generates_code128_svg(self, barcode_generator):
        config = BarcodeGenerationConfig(
            barcode_type="code128",
            value="ABC-12345",
            output_format="svg",
        )
        result = await barcode_generator.generate(config)
        assert result.content_type == "image/svg+xml"
        svg_str = result.data.decode("utf-8")
        assert "<svg" in svg_str


class TestBarcodeGeneratorEAN13:
    @pytest.mark.asyncio
    async def test_generates_ean13(self, barcode_generator):
        config = BarcodeGenerationConfig(
            barcode_type="ean13",
            value="5901234123457",
            output_format="png",
        )
        result = await barcode_generator.generate(config)
        assert result.content_type == "image/png"
        assert result.size_bytes > 0


class TestBarcodeGeneratorUnsupported:
    @pytest.mark.asyncio
    async def test_unsupported_type_raises(self, barcode_generator):
        config = BarcodeGenerationConfig(
            barcode_type="code128",
            value="test",
        )
        config_dict = config.model_dump()
        config_dict["barcode_type"] = "unknown_type"

        with pytest.raises(Exception):
            from qrcode_service.schemas.code import BarcodeGenerationConfig as BC
            BC(**config_dict)
