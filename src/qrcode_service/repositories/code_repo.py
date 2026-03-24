from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from qrcode_service.models.code import Code, CodeStatus


class CodeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, code: Code) -> Code:
        self._session.add(code)
        await self._session.commit()
        await self._session.refresh(code)
        return code

    async def get_by_id(self, code_id: uuid.UUID) -> Code | None:
        result = await self._session.execute(select(Code).where(Code.id == code_id))
        return result.scalar_one_or_none()

    async def get_by_short_code(self, short_code: str) -> Code | None:
        result = await self._session.execute(
            select(Code).where(Code.short_code == short_code)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_id: uuid.UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Code]:
        stmt = select(Code).where(Code.owner_id == owner_id)
        if status:
            stmt = stmt.where(Code.status == status)
        stmt = stmt.order_by(Code.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_owner(
        self, owner_id: uuid.UUID, status: str | None = None
    ) -> int:
        stmt = select(func.count()).select_from(Code).where(Code.owner_id == owner_id)
        if status:
            stmt = stmt.where(Code.status == status)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update_code(self, code_id: uuid.UUID, **kwargs) -> Code | None:
        await self._session.execute(
            update(Code).where(Code.id == code_id).values(**kwargs)
        )
        await self._session.commit()
        return await self.get_by_id(code_id)

    async def archive(self, code_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Code)
            .where(Code.id == code_id)
            .values(status=CodeStatus.ARCHIVED)
        )
        await self._session.commit()

    async def increment_scan_count(
        self, session: AsyncSession, code_id: uuid.UUID
    ) -> None:
        await session.execute(
            update(Code)
            .where(Code.id == code_id)
            .values(
                scan_count_total=Code.scan_count_total + 1,
                last_scanned_at=datetime.now(timezone.utc),
            )
        )

    async def short_code_exists(self, short_code: str) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(Code).where(Code.short_code == short_code)
        )
        return result.scalar_one() > 0
