from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime, timedelta, timezone

from user_agents import parse as parse_ua

from qrcode_service.database import get_async_session_factory
from qrcode_service.models.code import Code
from qrcode_service.models.scan_event import ScanEvent
from qrcode_service.repositories.code_repo import CodeRepository
from qrcode_service.config import get_settings


async def process_scan_event(ctx: dict, raw_payload: str) -> None:
    event_data = json.loads(raw_payload)
    settings = get_settings()

    ua_string = event_data.get("user_agent", "")
    ip = event_data.get("ip")

    device_type = None
    os_family = None
    browser_family = None
    if ua_string:
        ua = parse_ua(ua_string)
        if ua.is_mobile:
            device_type = "mobile"
        elif ua.is_tablet:
            device_type = "tablet"
        elif ua.is_pc:
            device_type = "desktop"
        else:
            device_type = "unknown"
        os_family = ua.os.family
        browser_family = ua.browser.family

    ip_hash = None
    if ip:
        daily_salt = date.today().isoformat()
        ip_hash = hashlib.sha256(
            f"{ip}{daily_salt}{settings.IP_HASH_SECRET.get_secret_value()}".encode()
        ).hexdigest()

    query_params = event_data.get("query_params", {})

    async with get_async_session_factory()() as session:
        code_id_raw = event_data.get("code_id")
        code_id = uuid.UUID(code_id_raw) if code_id_raw else None

        scan_event = ScanEvent(
            code_id=code_id,
            short_code=event_data["short_code"],
            ip_hash=ip_hash,
            device_type=device_type,
            os_family=os_family,
            browser_family=browser_family,
            referer=(event_data.get("referer") or "")[:500] or None,
            utm_source=query_params.get("utm_source"),
            utm_medium=query_params.get("utm_medium"),
            utm_campaign=query_params.get("utm_campaign"),
            scanned_at=datetime.fromisoformat(event_data["scanned_at"]),
        )
        session.add(scan_event)

        if code_id:
            repo = CodeRepository(session)
            await repo.increment_scan_count(session, code_id)

        await session.commit()


async def aggregate_daily_stats(ctx: dict) -> None:
    from sqlalchemy import select, func, update

    yesterday = date.today() - timedelta(days=1)
    seven_days_ago = date.today() - timedelta(days=7)
    thirty_days_ago = date.today() - timedelta(days=30)

    async with get_async_session_factory()() as session:
        codes_result = await session.execute(select(Code.id, Code.short_code))
        codes = codes_result.fetchall()

        for code_id, short_code in codes:
            count_7d_result = await session.execute(
                select(func.count())
                .select_from(ScanEvent)
                .where(
                    ScanEvent.code_id == code_id,
                    ScanEvent.scanned_at >= datetime.combine(
                        seven_days_ago, datetime.min.time(), tzinfo=timezone.utc
                    ),
                )
            )
            count_7d = count_7d_result.scalar_one()

            count_30d_result = await session.execute(
                select(func.count())
                .select_from(ScanEvent)
                .where(
                    ScanEvent.code_id == code_id,
                    ScanEvent.scanned_at >= datetime.combine(
                        thirty_days_ago, datetime.min.time(), tzinfo=timezone.utc
                    ),
                )
            )
            count_30d = count_30d_result.scalar_one()

            await session.execute(
                update(Code)
                .where(Code.id == code_id)
                .values(
                    scan_count_last_7d=count_7d,
                    scan_count_last_30d=count_30d,
                )
            )

        await session.commit()
