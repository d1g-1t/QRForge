from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from qrcode_service.api.dependencies import get_scan_service
from qrcode_service.models.code import CodeStatus
from qrcode_service.services.scan_service import ScanService

router = APIRouter()

PAUSED_PAGE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>QR Code Paused</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;
justify-content:center;height:100vh;margin:0;background:#f5f5f5}}
.c{{text-align:center;padding:2rem}}h1{{color:#333}}p{{color:#666}}</style>
</head><body><div class="c"><h1>QR Code Paused</h1>
<p>This QR code (<strong>{name}</strong>) is currently paused by its owner.</p>
</div></body></html>"""

TRANSPARENT_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
    b"\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


@router.get("/s/{short_code}", include_in_schema=False)
async def scan_redirect(
    request: Request,
    short_code: str,
    scan_service: Annotated[ScanService, Depends(get_scan_service)],
) -> Response:
    code_data = await scan_service.resolve(short_code)

    if not code_data:
        raise HTTPException(status_code=404, detail="QR code not found")

    if code_data.status == CodeStatus.PAUSED:
        return HTMLResponse(
            content=PAUSED_PAGE_HTML.format(name=code_data.name or short_code),
            status_code=200,
        )

    if code_data.status in (CodeStatus.ARCHIVED, CodeStatus.EXPIRED):
        raise HTTPException(status_code=410, detail="QR code no longer active")

    asyncio.create_task(
        scan_service.track_scan(
            code_id=code_data.id,
            short_code=short_code,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            referer=request.headers.get("Referer"),
            query_params=dict(request.query_params),
        )
    )

    return RedirectResponse(url=code_data.target_url, status_code=302)


@router.get("/s/{short_code}/pixel.gif", include_in_schema=False)
async def scan_pixel(
    request: Request,
    short_code: str,
    scan_service: Annotated[ScanService, Depends(get_scan_service)],
) -> Response:
    asyncio.create_task(
        scan_service.track_scan(
            code_id=None,
            short_code=short_code,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            is_pixel=True,
        )
    )

    return Response(
        content=TRANSPARENT_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )
