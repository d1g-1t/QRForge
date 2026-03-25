from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from qrcode_service.api.dependencies import get_code_service
from qrcode_service.schemas.code import BarcodeGenerationConfig, QRGenerationConfig
from qrcode_service.services.code_service import CodeService

router = APIRouter()


@router.post("/generate/qr")
async def generate_qr(
    content: Annotated[str, Form()],
    code_service: Annotated[CodeService, Depends(get_code_service)],
    error_correction: Annotated[str, Form()] = "H",
    output_format: Annotated[str, Form()] = "png",
    scale: Annotated[int, Form()] = 10,
    border: Annotated[int, Form()] = 4,
    dark_color: Annotated[str, Form()] = "#000000",
    light_color: Annotated[str, Form()] = "#FFFFFF",
    finder_dark: Annotated[str | None, Form()] = None,
    finder_light: Annotated[str | None, Form()] = None,
    logo_size_ratio: Annotated[float, Form()] = 0.25,
    logo_padding: Annotated[int, Form()] = 4,
    logo_round_corners: Annotated[bool, Form()] = True,
    logo_corner_radius: Annotated[int, Form()] = 8,
    boost_error_correction: Annotated[bool, Form()] = True,
    logo: Annotated[UploadFile | None, File()] = None,
) -> Response:
    config = QRGenerationConfig(
        content=content,
        error_correction=error_correction,
        output_format=output_format,
        scale=scale,
        border=border,
        dark_color=dark_color,
        light_color=light_color,
        finder_dark=finder_dark,
        finder_light=finder_light,
        logo_size_ratio=logo_size_ratio,
        logo_padding=logo_padding,
        logo_round_corners=logo_round_corners,
        logo_corner_radius=logo_corner_radius,
        boost_error_correction=boost_error_correction,
    )

    logo_bytes: bytes | None = None
    if logo:
        logo_bytes = await logo.read()

    result = await code_service.generate_qr_image(config, logo_bytes)

    return Response(
        content=result.data,
        media_type=result.content_type,
        headers={"X-QR-Version": str(result.qr_version or ""), "X-Size-Bytes": str(result.size_bytes)},
    )


@router.post("/generate/qr/preview")
async def generate_qr_preview(
    content: Annotated[str, Form()],
    code_service: Annotated[CodeService, Depends(get_code_service)],
    error_correction: Annotated[str, Form()] = "H",
    logo: Annotated[UploadFile | None, File()] = None,
) -> Response:
    config = QRGenerationConfig(
        content=content,
        error_correction=error_correction,
        output_format="png",
        scale=5,
        border=2,
    )

    logo_bytes: bytes | None = None
    if logo:
        logo_bytes = await logo.read()

    result = await code_service.generate_qr_image(config, logo_bytes)
    return Response(content=result.data, media_type="image/png")


@router.post("/generate/barcode")
async def generate_barcode(
    config: BarcodeGenerationConfig,
    code_service: Annotated[CodeService, Depends(get_code_service)],
) -> Response:
    result = await code_service.generate_barcode_image(config)
    return Response(content=result.data, media_type=result.content_type)
