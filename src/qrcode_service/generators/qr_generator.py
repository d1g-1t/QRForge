from __future__ import annotations

import asyncio
import base64
import re
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import segno
from PIL import Image

from qrcode_service.config import Settings
from qrcode_service.generators.logo_embedder import LogoEmbedder
from qrcode_service.schemas.code import GeneratedCode, QRGenerationConfig


class QRGenerator:
    def __init__(self, settings: Settings, logo_embedder: LogoEmbedder):
        self._settings = settings
        self._logo_embedder = logo_embedder
        self._executor = ThreadPoolExecutor(
            max_workers=settings.GENERATION_WORKERS,
            thread_name_prefix="qr-gen",
        )

    async def generate(
        self, config: QRGenerationConfig, logo: bytes | None = None
    ) -> GeneratedCode:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._generate_sync,
            config,
            logo,
        )

    def _generate_sync(
        self, config: QRGenerationConfig, logo: bytes | None
    ) -> GeneratedCode:
        qr = segno.make(
            config.content,
            error=config.error_correction.lower(),
            boost_error=config.boost_error_correction,
        )

        if config.output_format == "svg":
            return self._generate_svg(qr, config, logo)
        return self._generate_raster(qr, config, logo)

    def _generate_raster(
        self,
        qr: segno.QRCode,
        config: QRGenerationConfig,
        logo: bytes | None,
    ) -> GeneratedCode:
        buffer = BytesIO()
        qr.save(
            buffer,
            kind="png",
            scale=config.scale,
            border=config.border,
            dark=config.dark_color,
            light=config.light_color,
            finder_dark=config.finder_dark or config.dark_color,
            finder_light=config.finder_light or config.light_color,
        )
        buffer.seek(0)

        img = Image.open(buffer).convert("RGBA")

        if logo:
            img = self._logo_embedder.embed(
                qr_image=img,
                logo_bytes=logo,
                size_ratio=config.logo_size_ratio,
                padding=config.logo_padding,
                round_corners=config.logo_round_corners,
                corner_radius=config.logo_corner_radius,
            )

        output = BytesIO()
        if config.output_format == "webp":
            img.save(output, format="WEBP", quality=90, lossless=False)
            content_type = "image/webp"
        elif config.output_format == "pdf":
            img_rgb = img.convert("RGB")
            img_rgb.save(output, format="PDF")
            content_type = "application/pdf"
        else:
            img.save(output, format="PNG", optimize=True)
            content_type = "image/png"

        output_bytes = output.getvalue()

        return GeneratedCode(
            data=output_bytes,
            content_type=content_type,
            format=config.output_format,
            width=img.width,
            height=img.height,
            size_bytes=len(output_bytes),
            qr_version=qr.version,
            error_correction=str(qr.error).upper(),
        )

    def _generate_svg(
        self,
        qr: segno.QRCode,
        config: QRGenerationConfig,
        logo: bytes | None,
    ) -> GeneratedCode:
        buffer = BytesIO()
        qr.save(
            buffer,
            kind="svg",
            scale=config.scale,
            border=config.border,
            dark=config.dark_color,
            light=config.light_color,
            svgns=True,
            svgclass="qr-code",
            nl=False,
        )
        svg_bytes = buffer.getvalue()

        if logo:
            svg_bytes = self._embed_logo_in_svg(svg_bytes, config, logo)

        return GeneratedCode(
            data=svg_bytes,
            content_type="image/svg+xml",
            format="svg",
            size_bytes=len(svg_bytes),
            qr_version=qr.version,
            error_correction=str(qr.error).upper(),
        )

    def _embed_logo_in_svg(
        self,
        svg_bytes: bytes,
        config: QRGenerationConfig,
        logo: bytes,
    ) -> bytes:
        svg_str = svg_bytes.decode("utf-8")

        viewbox_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg_str)
        if viewbox_match:
            width = int(viewbox_match.group(1))
            height = int(viewbox_match.group(2))
        else:
            wh_match = re.search(
                r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', svg_str,
            )
            if not wh_match:
                return svg_bytes
            width = int(wh_match.group(1))
            height = int(wh_match.group(2))

        logo_w = int(width * config.logo_size_ratio)
        logo_h = int(height * config.logo_size_ratio)
        logo_x = (width - logo_w) // 2
        logo_y = (height - logo_h) // 2

        logo_b64 = base64.b64encode(logo).decode()

        logo_mime = "image/png"
        if logo[:4] == b"<svg" or logo[:5] == b"<?xml":
            logo_mime = "image/svg+xml"
        elif logo[:3] == b"\xff\xd8\xff":
            logo_mime = "image/jpeg"

        padding = config.logo_padding
        corner_radius = config.logo_corner_radius

        logo_element = (
            f'<rect x="{logo_x - padding}" '
            f'y="{logo_y - padding}" '
            f'width="{logo_w + padding * 2}" '
            f'height="{logo_h + padding * 2}" '
            f'fill="white" rx="{corner_radius}"/>'
            f'<image x="{logo_x}" y="{logo_y}" '
            f'width="{logo_w}" height="{logo_h}" '
            f'href="data:{logo_mime};base64,{logo_b64}" '
            f'preserveAspectRatio="xMidYMid meet"/>'
        )

        return svg_str.replace("</svg>", f"{logo_element}</svg>").encode("utf-8")
