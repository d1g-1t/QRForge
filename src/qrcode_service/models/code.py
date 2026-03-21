from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import ARRAY, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qrcode_service.database import Base


class CodeType(StrEnum):
    QR = "qr"
    BARCODE_EAN13 = "ean13"
    BARCODE_CODE128 = "code128"
    BARCODE_UPC = "upc"
    BARCODE_CODE39 = "code39"
    BARCODE_ISBN13 = "isbn13"


class CodeStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class Code(Base):
    __tablename__ = "codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    code_type: Mapped[str] = mapped_column(String(20), nullable=False)
    short_code: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False, index=True
    )

    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    barcode_value: Mapped[str | None] = mapped_column(String(255))

    generation_config: Mapped[dict] = mapped_column(JSONB, default=dict)

    status: Mapped[str] = mapped_column(
        String(20), default=CodeStatus.ACTIVE, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    scan_count_total: Mapped[int] = mapped_column(Integer, default=0)
    scan_count_last_7d: Mapped[int] = mapped_column(Integer, default=0)
    scan_count_last_30d: Mapped[int] = mapped_column(Integer, default=0)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    name: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    scan_events: Mapped[list["ScanEvent"]] = relationship(back_populates="code")
