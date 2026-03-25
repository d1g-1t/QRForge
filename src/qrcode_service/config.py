from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "QRForge"
    DEBUG: bool = False

    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    BASE_URL: str = "https://yourdomain.com"

    GENERATION_WORKERS: int = Field(default_factory=lambda: os.cpu_count() or 4)
    GENERATION_CACHE_TTL_SECONDS: int = 3600
    MAX_LOGO_SIZE_BYTES: int = 5 * 1024 * 1024

    SHORT_CODE_LENGTH: int = 8

    IP_HASH_SECRET: SecretStr
    GEOIP_DATABASE_PATH: str = "/data/GeoLite2-City.mmdb"

    SCAN_CACHE_TTL_SECONDS: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
