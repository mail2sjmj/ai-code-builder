"""
Application configuration via Pydantic BaseSettings.
All values are overridable via environment variables or a .env file.
"""

import logging
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:80"]
    )

    # ── File Upload ───────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, ge=1, le=500)
    ALLOWED_EXTENSIONS: list[str] = Field(default=[".csv", ".xlsx"])
    TEMP_DIR: str = "/tmp/code_builder_sessions"
    SESSION_TTL_SECONDS: int = Field(default=3600, ge=60)

    # ── Anthropic AI ──────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = Field(default="", description="Required in production")
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    REFINE_MAX_TOKENS: int = Field(default=2048, ge=256, le=8192)
    CODEGEN_MAX_TOKENS: int = Field(default=8192, ge=1024, le=32768)
    AI_TEMPERATURE: float = Field(default=0.2, ge=0.0, le=1.0)
    AI_REQUEST_TIMEOUT_SECONDS: int = Field(default=120, ge=10, le=600)

    # ── Sandbox Execution ─────────────────────────────────────────────────────
    SANDBOX_TIMEOUT_SECONDS: int = Field(default=30, ge=5, le=300)
    SANDBOX_MAX_MEMORY_MB: int = Field(default=512, ge=64, le=4096)
    SANDBOX_MAX_OUTPUT_ROWS: int = Field(default=100_000, ge=100)
    PREVIEW_ROW_COUNT: int = Field(default=50, ge=5, le=500)

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_extensions(cls, v: object) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v  # type: ignore[return-value]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v  # type: ignore[return-value]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    settings = Settings()
    logger.info(
        "Settings loaded: env=%s version=%s model=%s",
        settings.APP_ENV,
        settings.APP_VERSION,
        settings.ANTHROPIC_MODEL,
    )
    return settings
