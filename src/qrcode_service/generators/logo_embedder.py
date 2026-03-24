from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw


class LogoEmbedder:
    def embed(
        self,
        qr_image: Image.Image,
        logo_bytes: bytes,
        size_ratio: float,
        padding: int,
        round_corners: bool,
        corner_radius: int,
    ) -> Image.Image:
        logo = self._load_logo(logo_bytes)

        qr_w, qr_h = qr_image.size
        max_logo_size = int(min(qr_w, qr_h) * size_ratio)
        logo = self._resize_logo(logo, max_logo_size)

        if round_corners:
            logo = self._apply_rounded_corners(logo, corner_radius)

        logo_w, logo_h = logo.size
        bg_w = logo_w + padding * 2
        bg_h = logo_h + padding * 2

        bg = Image.new("RGBA", (bg_w, bg_h), (255, 255, 255, 255))
        if round_corners:
            bg = self._apply_rounded_corners(bg, corner_radius + padding)

        logo_paste_pos = (padding, padding)
        bg.paste(logo, logo_paste_pos, mask=logo if logo.mode == "RGBA" else None)

        result = qr_image.copy()
        pos_x = (qr_w - bg_w) // 2
        pos_y = (qr_h - bg_h) // 2
        result.paste(bg, (pos_x, pos_y), mask=bg)

        return result

    def _load_logo(self, logo_bytes: bytes) -> Image.Image:
        if logo_bytes[:4] in (b"<svg", b"<?xm") or b"<svg" in logo_bytes[:100]:
            import cairosvg

            png_bytes = cairosvg.svg2png(
                bytestring=logo_bytes,
                output_width=500,
            )
            return Image.open(BytesIO(png_bytes)).convert("RGBA")

        img = Image.open(BytesIO(logo_bytes))

        if getattr(img, "is_animated", False):
            img.seek(0)

        return img.convert("RGBA")

    def _resize_logo(self, logo: Image.Image, max_size: int) -> Image.Image:
        w, h = logo.size
        if w == 0 or h == 0:
            raise ValueError("Logo has zero dimensions")

        ratio = min(max_size / w, max_size / h)
        new_w = max(1, int(w * ratio))
        new_h = max(1, int(h * ratio))

        return logo.resize((new_w, new_h), Image.LANCZOS)

    def _apply_rounded_corners(self, img: Image.Image, radius: int) -> Image.Image:
        if radius <= 0:
            return img

        img = img.convert("RGBA")
        w, h = img.size

        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)

        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        result.paste(img, mask=mask)
        return result

    def validate_logo_size(
        self, logo_bytes: bytes, size_ratio: float
    ) -> tuple[bool, str | None]:
        if len(logo_bytes) > 5 * 1024 * 1024:
            return False, "Logo exceeds 5MB limit"

        if size_ratio > 0.30:
            return False, (
                "Logo size ratio exceeds 30% — QR will be unreadable. "
                "Reduce logo_size_ratio or use error_correction=H"
            )

        return True, None
