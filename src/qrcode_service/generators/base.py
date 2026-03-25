from __future__ import annotations

from typing import Protocol, runtime_checkable

from qrcode_service.schemas.code import GeneratedCode


@runtime_checkable
class BaseGenerator(Protocol):
    async def generate(self, config: object) -> GeneratedCode: ...
