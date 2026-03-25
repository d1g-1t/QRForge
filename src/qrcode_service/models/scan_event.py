from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qrcode_service.database import Base


class ScanEvent(Base):
    __tablename__ = "scan_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("codes.id"), index=True
    )
    short_code: Mapped[str] = mapped_column(String(12), nullable=False, index=True)

    ip_hash: Mapped[str | None] = mapped_column(String(64))

    country_code: Mapped[str | None] = mapped_column(String(2))
    city: Mapped[str | None] = mapped_column(String(100))

    device_type: Mapped[str | None] = mapped_column(String(20))
    os_family: Mapped[str | None] = mapped_column(String(50))
    browser_family: Mapped[str | None] = mapped_column(String(50))

    referer: Mapped[str | None] = mapped_column(String(500))

    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    code: Mapped["Code"] = relationship(back_populates="scan_events")
