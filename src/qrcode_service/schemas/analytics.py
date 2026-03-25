from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    count: int


class GeoStat(BaseModel):
    country_code: str
    city: str | None = None
    count: int


class DeviceStat(BaseModel):
    category: str
    value: str
    count: int


class HeatmapPoint(BaseModel):
    day_of_week: int
    hour: int
    count: int


class ScanStats(BaseModel):
    total_scans: int
    time_series: list[TimeSeriesPoint]
    geo_distribution: list[GeoStat]
    device_breakdown: list[DeviceStat]
    period_from: datetime
    period_to: datetime
