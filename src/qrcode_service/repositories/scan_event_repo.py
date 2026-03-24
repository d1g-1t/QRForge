from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, func, text, extract
from sqlalchemy.ext.asyncio import AsyncSession

from qrcode_service.models.scan_event import ScanEvent


class ScanEventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: ScanEvent) -> ScanEvent:
        self._session.add(event)
        await self._session.commit()
        return event

    async def get_time_series(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        bucket: str = "day",
    ) -> list[tuple[datetime, int]]:
        bucket_map = {
            "hour": "hour",
            "day": "day",
            "week": "week",
            "month": "month",
        }
        trunc_val = bucket_map.get(bucket, "day")

        stmt = (
            select(
                func.date_trunc(trunc_val, ScanEvent.scanned_at).label("bucket"),
                func.count().label("scan_count"),
            )
            .where(
                ScanEvent.code_id == code_id,
                ScanEvent.scanned_at >= from_dt,
                ScanEvent.scanned_at <= to_dt,
            )
            .group_by(text("bucket"))
            .order_by(text("bucket"))
        )
        result = await self._session.execute(stmt)
        return [(row.bucket, row.scan_count) for row in result.fetchall()]

    async def get_geo_stats(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        limit: int = 20,
    ) -> list[tuple[str, str | None, int]]:
        stmt = (
            select(
                ScanEvent.country_code,
                ScanEvent.city,
                func.count().label("cnt"),
            )
            .where(
                ScanEvent.code_id == code_id,
                ScanEvent.scanned_at >= from_dt,
                ScanEvent.scanned_at <= to_dt,
                ScanEvent.country_code.isnot(None),
            )
            .group_by(ScanEvent.country_code, ScanEvent.city)
            .order_by(text("cnt DESC"))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row.country_code, row.city, row.cnt) for row in result.fetchall()]

    async def get_device_stats(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[tuple[str, str, int]]:
        rows: list[tuple[str, str, int]] = []

        for col, category in [
            (ScanEvent.device_type, "device_type"),
            (ScanEvent.os_family, "os_family"),
            (ScanEvent.browser_family, "browser_family"),
        ]:
            stmt = (
                select(col, func.count().label("cnt"))
                .where(
                    ScanEvent.code_id == code_id,
                    ScanEvent.scanned_at >= from_dt,
                    ScanEvent.scanned_at <= to_dt,
                    col.isnot(None),
                )
                .group_by(col)
                .order_by(text("cnt DESC"))
                .limit(10)
            )
            result = await self._session.execute(stmt)
            for row in result.fetchall():
                rows.append((category, row[0], row.cnt))

        return rows

    async def get_heatmap(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[tuple[int, int, int]]:
        stmt = (
            select(
                extract("dow", ScanEvent.scanned_at).label("dow"),
                extract("hour", ScanEvent.scanned_at).label("hour"),
                func.count().label("cnt"),
            )
            .where(
                ScanEvent.code_id == code_id,
                ScanEvent.scanned_at >= from_dt,
                ScanEvent.scanned_at <= to_dt,
            )
            .group_by(text("dow"), text("hour"))
            .order_by(text("dow"), text("hour"))
        )
        result = await self._session.execute(stmt)
        return [(int(row.dow), int(row.hour), row.cnt) for row in result.fetchall()]
