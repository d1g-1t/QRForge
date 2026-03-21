from __future__ import annotations

from arq import cron
from arq.connections import RedisSettings

from qrcode_service.config import get_settings
from qrcode_service.worker.tasks import aggregate_daily_stats, process_scan_event


_settings = get_settings()
_redis_url = str(_settings.REDIS_URL)

_host = "localhost"
_port = 6379
_database = 0

if "://" in _redis_url:
    from urllib.parse import urlparse
    _parsed = urlparse(_redis_url)
    _host = _parsed.hostname or "localhost"
    _port = _parsed.port or 6379
    _database = int((_parsed.path or "/0").lstrip("/") or "0")


class WorkerSettings:
    functions = [process_scan_event]
    cron_jobs = [
        cron(aggregate_daily_stats, hour=0, minute=5),
    ]
    redis_settings = RedisSettings(host=_host, port=_port, database=_database)
    max_jobs = 50
    job_timeout = 60
