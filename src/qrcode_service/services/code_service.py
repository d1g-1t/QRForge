from __future__ import annotations

import hashlib
import secrets
import string
import uuid

import redis.asyncio as redis

from qrcode_service.config import Settings
from qrcode_service.generators.barcode_generator import BarcodeGenerator
from qrcode_service.generators.qr_generator import QRGenerator
from qrcode_service.models.code import Code, CodeType
from qrcode_service.repositories.code_repo import CodeRepository
from qrcode_service.schemas.code import (
    BarcodeGenerationConfig,
    CodeCreate,
    CodeResponse,
    CodeUpdate,
    GeneratedCode,
    QRGenerationConfig,
)

_BASE62 = string.ascii_letters + string.digits


class CodeService:
    def __init__(
        self,
        settings: Settings,
        code_repo: CodeRepository,
        qr_generator: QRGenerator,
        barcode_generator: BarcodeGenerator,
        redis_client: redis.Redis,
        redis_binary: redis.Redis,
    ):
        self._settings = settings
        self._code_repo = code_repo
        self._qr_generator = qr_generator
        self._barcode_generator = barcode_generator
        self._redis = redis_client
        self._redis_binary = redis_binary

    async def create_code(
        self,
        owner_id: uuid.UUID,
        data: CodeCreate,
        logo: bytes | None = None,
    ) -> CodeResponse:
        short_code = await self._generate_unique_short_code()

        generation_config: dict = {}
        if data.qr_config:
            generation_config = data.qr_config.model_dump()
            generation_config["has_logo"] = logo is not None
            if logo:
                generation_config["logo_hash"] = hashlib.sha256(logo).hexdigest()[:16]
        elif data.barcode_config:
            generation_config = data.barcode_config.model_dump()

        code = Code(
            owner_id=owner_id,
            code_type=data.code_type,
            short_code=short_code,
            target_url=data.target_url,
            barcode_value=data.barcode_config.value if data.barcode_config else None,
            generation_config=generation_config,
            name=data.name,
            tags=data.tags,
            expires_at=data.expires_at,
        )
        code = await self._code_repo.create(code)

        base_url = self._settings.BASE_URL.rstrip("/")
        response = CodeResponse.model_validate(code)
        response.scan_url = f"{base_url}/s/{short_code}"
        response.qr_image_url = f"{base_url}/api/v1/codes/{code.id}/image"
        return response

    async def get_code(self, code_id: uuid.UUID) -> CodeResponse | None:
        code = await self._code_repo.get_by_id(code_id)
        if not code:
            return None

        redis_total = await self._redis.get(f"qr:scans:total:{code.short_code}")
        response = CodeResponse.model_validate(code)
        if redis_total:
            response.scan_count_total = max(code.scan_count_total, int(redis_total))

        base_url = self._settings.BASE_URL.rstrip("/")
        response.scan_url = f"{base_url}/s/{code.short_code}"
        response.qr_image_url = f"{base_url}/api/v1/codes/{code.id}/image"
        return response

    async def list_codes(
        self,
        owner_id: uuid.UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[CodeResponse], int]:
        codes = await self._code_repo.list_by_owner(owner_id, status, offset, limit)
        total = await self._code_repo.count_by_owner(owner_id, status)
        base_url = self._settings.BASE_URL.rstrip("/")

        responses = []
        for code in codes:
            resp = CodeResponse.model_validate(code)
            resp.scan_url = f"{base_url}/s/{code.short_code}"
            resp.qr_image_url = f"{base_url}/api/v1/codes/{code.id}/image"
            responses.append(resp)

        return responses, total

    async def update_code(
        self, code_id: uuid.UUID, data: CodeUpdate
    ) -> CodeResponse | None:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_code(code_id)

        code = await self._code_repo.update_code(code_id, **update_data)
        if not code:
            return None

        await self._redis.delete(f"qr:code:{code.short_code}")

        base_url = self._settings.BASE_URL.rstrip("/")
        response = CodeResponse.model_validate(code)
        response.scan_url = f"{base_url}/s/{code.short_code}"
        response.qr_image_url = f"{base_url}/api/v1/codes/{code.id}/image"
        return response

    async def archive_code(self, code_id: uuid.UUID) -> bool:
        code = await self._code_repo.get_by_id(code_id)
        if not code:
            return False
        await self._code_repo.archive(code_id)
        await self._redis.delete(f"qr:code:{code.short_code}")
        return True

    async def generate_qr_image(
        self,
        config: QRGenerationConfig,
        logo: bytes | None = None,
    ) -> GeneratedCode:
        cache_key = self._generation_cache_key(config, logo)
        cached = await self._redis_binary.get(cache_key)
        if cached:
            return GeneratedCode(
                data=cached,
                content_type=self._content_type_for_format(config.output_format),
                format=config.output_format,
                size_bytes=len(cached),
            )

        result = await self._qr_generator.generate(config, logo)

        await self._redis_binary.setex(
            cache_key,
            self._settings.GENERATION_CACHE_TTL_SECONDS,
            result.data,
        )
        return result

    async def generate_barcode_image(
        self, config: BarcodeGenerationConfig
    ) -> GeneratedCode:
        cache_key = self._generation_cache_key(config, None)
        cached = await self._redis_binary.get(cache_key)
        if cached:
            return GeneratedCode(
                data=cached,
                content_type=self._content_type_for_format(config.output_format),
                format=config.output_format,
                size_bytes=len(cached),
            )

        result = await self._barcode_generator.generate(config)

        await self._redis_binary.setex(
            cache_key,
            self._settings.GENERATION_CACHE_TTL_SECONDS,
            result.data,
        )
        return result

    async def get_code_image(
        self,
        code_id: uuid.UUID,
        output_format: str = "png",
        scale: int = 10,
    ) -> GeneratedCode | None:
        code = await self._code_repo.get_by_id(code_id)
        if not code:
            return None

        if code.code_type in (
            CodeType.BARCODE_EAN13,
            CodeType.BARCODE_CODE128,
            CodeType.BARCODE_UPC,
            CodeType.BARCODE_CODE39,
            CodeType.BARCODE_ISBN13,
        ):
            bc_format = "svg" if output_format == "svg" else "png"
            config = BarcodeGenerationConfig(
                barcode_type=code.code_type,
                value=code.barcode_value or code.target_url,
                output_format=bc_format,
            )
            return await self.generate_barcode_image(config)

        config = QRGenerationConfig(
            content=code.target_url,
            output_format=output_format,
            scale=scale,
        )
        return await self.generate_qr_image(config)

    def _generation_cache_key(
        self,
        config: QRGenerationConfig | BarcodeGenerationConfig,
        logo: bytes | None,
    ) -> str:
        config_json = config.model_dump_json()
        logo_hash = (
            hashlib.sha256(logo).hexdigest()[:16] if logo else "nologo"
        )
        content_hash = hashlib.sha256(
            f"{config_json}{logo_hash}".encode()
        ).hexdigest()
        return f"qr:gen:{content_hash}"

    @staticmethod
    def _content_type_for_format(fmt: str) -> str:
        return {
            "png": "image/png",
            "svg": "image/svg+xml",
            "webp": "image/webp",
            "pdf": "application/pdf",
        }.get(fmt, "image/png")

    async def _generate_unique_short_code(self) -> str:
        length = self._settings.SHORT_CODE_LENGTH
        for _ in range(100):
            code = "".join(secrets.choice(_BASE62) for _ in range(length))
            if not await self._code_repo.short_code_exists(code):
                return code
        raise RuntimeError("Failed to generate unique short code after 100 attempts")
