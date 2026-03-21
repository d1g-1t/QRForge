from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from qrcode_service.api.dependencies import get_code_service, get_current_owner_id
from qrcode_service.schemas.code import CodeCreate, CodeResponse, CodeUpdate
from qrcode_service.services.code_service import CodeService

router = APIRouter()


@router.post("/codes", response_model=CodeResponse, status_code=201)
async def create_code(
    data: CodeCreate,
    code_service: Annotated[CodeService, Depends(get_code_service)],
    owner_id: Annotated[uuid.UUID, Depends(get_current_owner_id)],
) -> CodeResponse:
    return await code_service.create_code(owner_id, data)


@router.get("/codes", response_model=list[CodeResponse])
async def list_codes(
    code_service: Annotated[CodeService, Depends(get_code_service)],
    owner_id: Annotated[uuid.UUID, Depends(get_current_owner_id)],
    status: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CodeResponse]:
    codes, _ = await code_service.list_codes(owner_id, status, offset, limit)
    return codes


@router.get("/codes/{code_id}", response_model=CodeResponse)
async def get_code(
    code_id: uuid.UUID,
    code_service: Annotated[CodeService, Depends(get_code_service)],
) -> CodeResponse:
    result = await code_service.get_code(code_id)
    if not result:
        raise HTTPException(status_code=404, detail="Code not found")
    return result


@router.patch("/codes/{code_id}", response_model=CodeResponse)
async def update_code(
    code_id: uuid.UUID,
    data: CodeUpdate,
    code_service: Annotated[CodeService, Depends(get_code_service)],
) -> CodeResponse:
    result = await code_service.update_code(code_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Code not found")
    return result


@router.delete("/codes/{code_id}", status_code=204)
async def delete_code(
    code_id: uuid.UUID,
    code_service: Annotated[CodeService, Depends(get_code_service)],
) -> None:
    success = await code_service.archive_code(code_id)
    if not success:
        raise HTTPException(status_code=404, detail="Code not found")


@router.get("/codes/{code_id}/image")
async def get_code_image(
    code_id: uuid.UUID,
    code_service: Annotated[CodeService, Depends(get_code_service)],
    format: Annotated[str, Query()] = "png",
    scale: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Response:
    result = await code_service.get_code_image(code_id, format, scale)
    if not result:
        raise HTTPException(status_code=404, detail="Code not found")
    return Response(content=result.data, media_type=result.content_type)
