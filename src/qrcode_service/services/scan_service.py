from __future__ import annotations

from datetime import date

import redis.asyncio as redis

from qrcode_service.config import Settings
from qrcode_service.models.code import CodeStatus
from qrcode_service.repositories.code_repo import CodeRepository
from qrcode_service.schemas.code import CodeCacheEntry


class ScanService:
    def __init__(
        self,
        settings: Settings,
        code_repo: CodeRepository,
        redis_client: redis.Redis,
    ):
        self._settings = settings
        self._code_repo = code_repo
        self._redis = redis_client

    async def resolve(self, short_code: str) -> CodeCacheEntry | None:
        cache_key = f"qr:code:{short_code}"

        cached = await self._redis.get(cache_key)
        if cached:
            if '{"not_found"' in cached or '"not_found": true' in cached:
                return None
            entry = CodeCacheEntry.model_validate_json(cached)
            if entry.not_found:
                return None
            return entry

        code = await self._code_repo.get_by_short_code(short_code)
        if not code:
            await self._redis.setex(cache_key, 30, '{"not_found": true}')
            return None

        entry = CodeCacheEntry(
            id=str(code.id),
            target_url=code.target_url,
            status=code.status,
            name=code.name,
        )
        await self._redis.setex(
            cache_key,
            self._settings.SCAN_CACHE_TTL_SECONDS,
            entry.model_dump_json(),
        )
        return entry

    async def track_scan(
        self,
        code_id: str | None,
        short_code: str,
        ip: str | None,
        user_agent: str | None = None,
        referer: str | None = None,
        query_params: dict | None = None,
        is_pixel: bool = False,
    ) -> None:
        try:
            today_key = f"qr:scans:today:{short_code}:{date.today().isoformat()}"
            pipe = self._redis.pipeline()
            pipe.incr(f"qr:scans:total:{short_code}")
            pipe.incr(today_key)
            pipe.expire(today_key, 86400 * 2)
            await pipe.execute()

            await self._redis.rpush(
                "qr:scan_queue",
                CodeCacheEntry(
                    id=code_id or "",
                    target_url="",
                    status="",
                ).model_dump_json()
                if False
                else self._build_event_payload(
                    code_id, short_code, ip, user_agent, referer, query_params, is_pixel
                ),
            )
        except Exception:
            pass

    def _build_event_payload(
        self,
        code_id: str | None,
        short_code: str,
        ip: str | None,
        user_agent: str | None,
        referer: str | None,
        query_params: dict | None,
        is_pixel: bool,
    ) -> str:
        import json
        from datetime import datetime, timezone

        return json.dumps(
            {
                "code_id": code_id,
                "short_code": short_code,
                "ip": ip,
                "user_agent": user_agent,
                "referer": referer,
                "query_params": query_params or {},
                "is_pixel": is_pixel,
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            }
        )
