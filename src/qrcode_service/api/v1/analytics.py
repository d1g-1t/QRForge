from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from qrcode_service.api.dependencies import get_analytics_service
from qrcode_service.schemas.analytics import (
    DeviceStat,
    GeoStat,
    HeatmapPoint,
    ScanStats,
)
from qrcode_service.services.analytics_service import AnalyticsService

router = APIRouter()


def _default_from() -> datetime:
    return datetime(2020, 1, 1, tzinfo=timezone.utc)


def _default_to() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/codes/{code_id}/stats", response_model=ScanStats)
async def get_scan_stats(
    code_id: uuid.UUID,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_dt: Annotated[datetime | None, Query(alias="from")] = None,
    to_dt: Annotated[datetime | None, Query(alias="to")] = None,
    bucket: Annotated[str, Query()] = "day",
) -> ScanStats:
    return await analytics_service.get_scan_stats(
        code_id,
        from_dt or _default_from(),
        to_dt or _default_to(),
        bucket,
    )


@router.get("/codes/{code_id}/stats/geo", response_model=list[GeoStat])
async def get_geo_stats(
    code_id: uuid.UUID,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_dt: Annotated[datetime | None, Query(alias="from")] = None,
    to_dt: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[GeoStat]:
    return await analytics_service.get_geo_stats(
        code_id,
        from_dt or _default_from(),
        to_dt or _default_to(),
    )


@router.get("/codes/{code_id}/stats/devices", response_model=list[DeviceStat])
async def get_device_stats(
    code_id: uuid.UUID,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_dt: Annotated[datetime | None, Query(alias="from")] = None,
    to_dt: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[DeviceStat]:
    return await analytics_service.get_device_stats(
        code_id,
        from_dt or _default_from(),
        to_dt or _default_to(),
    )


@router.get("/codes/{code_id}/stats/heatmap", response_model=list[HeatmapPoint])
async def get_heatmap(
    code_id: uuid.UUID,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_dt: Annotated[datetime | None, Query(alias="from")] = None,
    to_dt: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[HeatmapPoint]:
    return await analytics_service.get_heatmap(
        code_id,
        from_dt or _default_from(),
        to_dt or _default_to(),
    )
