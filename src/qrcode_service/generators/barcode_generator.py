from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import barcode
from barcode.writer import ImageWriter, SVGWriter

from qrcode_service.config import Settings
from qrcode_service.schemas.code import BarcodeGenerationConfig, GeneratedCode

BARCODE_CLASS_MAP = {
    "ean13": "EAN13",
    "ean8": "EAN8",
    "code128": "Code128",
    "code39": "Code39",
    "upc": "UPCA",
    "isbn13": "ISBN13",
    "isbn10": "ISBN10",
    "gs1_128": "Gs1_128",
}


class BarcodeGenerator:
    def __init__(self, settings: Settings):
        self._executor = ThreadPoolExecutor(
            max_workers=settings.GENERATION_WORKERS,
            thread_name_prefix="bc-gen",
        )

    async def generate(self, config: BarcodeGenerationConfig) -> GeneratedCode:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._generate_sync,
            config,
        )

    def _generate_sync(self, config: BarcodeGenerationConfig) -> GeneratedCode:
        barcode_class_name = BARCODE_CLASS_MAP.get(config.barcode_type)
        if not barcode_class_name:
            raise ValueError(f"Unsupported barcode type: {config.barcode_type}")

        barcode_cls = barcode.get_barcode_class(barcode_class_name)

        writer_options = {
            "module_width": config.module_width,
            "module_height": config.module_height,
            "quiet_zone": config.quiet_zone,
            "write_text": config.write_text,
            "text_distance": config.text_distance,
            "font_size": config.font_size,
            "foreground": config.foreground,
            "background": config.background,
        }

        buffer = BytesIO()

        if config.output_format == "svg":
            writer = SVGWriter()
            bc = barcode_cls(config.value, writer=writer)
            bc.write(buffer, options=writer_options)
            content_type = "image/svg+xml"
        else:
            writer = ImageWriter()
            bc = barcode_cls(config.value, writer=writer)
            bc.write(buffer, options=writer_options)
            content_type = "image/png"

        output_bytes = buffer.getvalue()

        return GeneratedCode(
            data=output_bytes,
            content_type=content_type,
            format=config.output_format,
            size_bytes=len(output_bytes),
        )
