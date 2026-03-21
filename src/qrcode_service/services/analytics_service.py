from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from qrcode_service.repositories.scan_event_repo import ScanEventRepository
from qrcode_service.schemas.analytics import (
    DeviceStat,
    GeoStat,
    HeatmapPoint,
    ScanStats,
    TimeSeriesPoint,
)


class AnalyticsService:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        redis_client: redis.Redis,
    ):
        self._session_factory = session_factory
        self._redis = redis_client

    async def get_scan_stats(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        bucket: Literal["hour", "day", "week", "month"] = "day",
    ) -> ScanStats:
        async with self._session_factory() as session:
            repo = ScanEventRepository(session)

            time_series_raw = await repo.get_time_series(
                code_id, from_dt, to_dt, bucket
            )
            time_series = [
                TimeSeriesPoint(timestamp=ts, count=cnt)
                for ts, cnt in time_series_raw
            ]

            geo_raw = await repo.get_geo_stats(code_id, from_dt, to_dt)
            geo_stats = [
                GeoStat(country_code=cc, city=city, count=cnt)
                for cc, city, cnt in geo_raw
            ]

            device_raw = await repo.get_device_stats(code_id, from_dt, to_dt)
            device_stats = [
                DeviceStat(category=cat, value=val, count=cnt)
                for cat, val, cnt in device_raw
            ]

            total = await self._redis.get(f"qr:scans:total:{code_id}")

            return ScanStats(
                total_scans=int(total or 0),
                time_series=time_series,
                geo_distribution=geo_stats,
                device_breakdown=device_stats,
                period_from=from_dt,
                period_to=to_dt,
            )

    async def get_geo_stats(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[GeoStat]:
        async with self._session_factory() as session:
            repo = ScanEventRepository(session)
            raw = await repo.get_geo_stats(code_id, from_dt, to_dt)
            return [
                GeoStat(country_code=cc, city=city, count=cnt)
                for cc, city, cnt in raw
            ]

    async def get_device_stats(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[DeviceStat]:
        async with self._session_factory() as session:
            repo = ScanEventRepository(session)
            raw = await repo.get_device_stats(code_id, from_dt, to_dt)
            return [
                DeviceStat(category=cat, value=val, count=cnt)
                for cat, val, cnt in raw
            ]

    async def get_heatmap(
        self,
        code_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[HeatmapPoint]:
        async with self._session_factory() as session:
            repo = ScanEventRepository(session)
            raw = await repo.get_heatmap(code_id, from_dt, to_dt)
            return [
                HeatmapPoint(day_of_week=dow, hour=hour, count=cnt)
                for dow, hour, cnt in raw
            ]
