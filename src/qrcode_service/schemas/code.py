from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QRGenerationConfig(BaseModel):
    content: str = Field(..., min_length=1, max_length=4296)
    error_correction: Literal["L", "M", "Q", "H"] = "H"
    output_format: Literal["png", "svg", "webp", "pdf"] = "png"
    scale: int = Field(default=10, ge=1, le=50)
    border: int = Field(default=4, ge=0, le=20)
    dark_color: str = Field(default="#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    light_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    finder_dark: str | None = None
    finder_light: str | None = None
    logo_size_ratio: float = Field(default=0.25, ge=0.05, le=0.30)
    logo_padding: int = Field(default=4, ge=0, le=20)
    logo_round_corners: bool = True
    logo_corner_radius: int = 8
    boost_error_correction: bool = True


class BarcodeGenerationConfig(BaseModel):
    barcode_type: Literal[
        "ean13", "ean8", "code128", "code39", "upc", "isbn13", "isbn10", "gs1_128"
    ] = "code128"
    value: str = Field(..., min_length=1)
    output_format: Literal["png", "svg"] = "png"
    module_width: float = Field(default=10.0, ge=1.0, le=50.0)
    module_height: float = Field(default=10.0, ge=5.0, le=50.0)
    quiet_zone: float = Field(default=6.5, ge=0.0)
    write_text: bool = True
    text_distance: float = 5.0
    font_size: int = Field(default=10, ge=6, le=24)
    foreground: str = Field(default="#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    background: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")


class GeneratedCode(BaseModel):
    data: bytes
    content_type: str
    format: str
    width: int | None = None
    height: int | None = None
    size_bytes: int
    qr_version: str | int | None = None
    error_correction: str | None = None


class LogoValidationResult(BaseModel):
    valid: bool
    error: str | None = None


class CodeCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4296)
    name: str | None = None
    tags: list[str] = Field(default_factory=list)
    target_url: str = Field(..., min_length=1, max_length=2048)
    expires_at: datetime | None = None
    code_type: str = "qr"
    qr_config: QRGenerationConfig | None = None
    barcode_config: BarcodeGenerationConfig | None = None


class BarcodeCreate(BaseModel):
    value: str = Field(..., min_length=1)
    name: str | None = None
    tags: list[str] = Field(default_factory=list)
    target_url: str = Field(..., min_length=1, max_length=2048)
    expires_at: datetime | None = None
    barcode_config: BarcodeGenerationConfig


class CodeUpdate(BaseModel):
    target_url: str | None = Field(default=None, max_length=2048)
    name: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    expires_at: datetime | None = None


class CodeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    owner_id: uuid.UUID
    code_type: str
    short_code: str
    target_url: str
    barcode_value: str | None = None
    status: str
    expires_at: datetime | None = None
    scan_count_total: int = 0
    scan_count_last_7d: int = 0
    scan_count_last_30d: int = 0
    last_scanned_at: datetime | None = None
    name: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None = None
    scan_url: str | None = None
    qr_image_url: str | None = None


class CodeCacheEntry(BaseModel):
    id: str
    target_url: str
    status: str
    name: str | None = None
    not_found: bool = False
