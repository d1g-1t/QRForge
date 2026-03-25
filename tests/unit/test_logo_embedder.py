import pytest
from io import BytesIO

from PIL import Image

from qrcode_service.generators.logo_embedder import LogoEmbedder


@pytest.fixture
def embedder():
    return LogoEmbedder()


@pytest.fixture
def qr_image():
    return Image.new("RGBA", (330, 330), (255, 255, 255, 255))


@pytest.fixture
def logo_bytes_small():
    img = Image.new("RGBA", (50, 50), (255, 0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestLogoEmbedding:
    def test_embeds_logo_at_center(self, embedder, qr_image, logo_bytes_small):
        result = embedder.embed(
            qr_image=qr_image,
            logo_bytes=logo_bytes_small,
            size_ratio=0.25,
            padding=4,
            round_corners=False,
            corner_radius=0,
        )
        assert result.size == qr_image.size
        center_pixel = result.getpixel((165, 165))
        assert center_pixel != (255, 255, 255, 255)

    def test_logo_covers_under_30_percent(self, embedder, qr_image, logo_bytes_small):
        result = embedder.embed(
            qr_image=qr_image,
            logo_bytes=logo_bytes_small,
            size_ratio=0.25,
            padding=4,
            round_corners=False,
            corner_radius=0,
        )

        qr_area = qr_image.width * qr_image.height
        logo_max_size = int(min(qr_image.width, qr_image.height) * 0.25)
        logo_area = logo_max_size * logo_max_size
        assert logo_area / qr_area <= 0.30

    def test_rounded_corners(self, embedder, qr_image, logo_bytes_small):
        result = embedder.embed(
            qr_image=qr_image,
            logo_bytes=logo_bytes_small,
            size_ratio=0.25,
            padding=4,
            round_corners=True,
            corner_radius=8,
        )
        assert result.size == qr_image.size


class TestLogoValidation:
    def test_valid_logo(self, embedder):
        valid, error = embedder.validate_logo_size(b"x" * 1000, 0.25)
        assert valid is True
        assert error is None

    def test_logo_too_large(self, embedder):
        valid, error = embedder.validate_logo_size(b"x" * (6 * 1024 * 1024), 0.25)
        assert valid is False
        assert "5MB" in error

    def test_logo_ratio_too_high(self, embedder):
        valid, error = embedder.validate_logo_size(b"x" * 100, 0.35)
        assert valid is False
        assert "30%" in error


class TestLogoLoading:
    def test_loads_png(self, embedder, logo_bytes_small):
        img = embedder._load_logo(logo_bytes_small)
        assert img.mode == "RGBA"

    def test_loads_jpeg(self, embedder):
        img = Image.new("RGB", (50, 50), (255, 0, 0))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        result = embedder._load_logo(buf.getvalue())
        assert result.mode == "RGBA"

    def test_resize_maintains_aspect(self, embedder):
        img = Image.new("RGBA", (200, 100), (0, 0, 0, 255))
        resized = embedder._resize_logo(img, 50)
        assert resized.width == 50
        assert resized.height == 25

    def test_resize_zero_dimensions_raises(self, embedder):
        img = Image.new("RGBA", (0, 0))
        with pytest.raises(ValueError, match="zero dimensions"):
            embedder._resize_logo(img, 50)
