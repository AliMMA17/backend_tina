"""Application configuration using pydantic-settings.

Decision: Centralized, typed configuration loaded from environment variables
and .env files. This keeps secrets out of code and makes the service
12-factor compliant — essential for microservices running in containers.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "FastAPI Clean Template"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Security
    secret_key: SecretStr = Field(
        default=SecretStr("dev-secret-key-change-in-production-min-32-chars"),
        description="JWT signing key — must be a long random string in production",
    )
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/app",
        description="Async PostgreSQL connection string (postgresql+asyncpg://...)",
    )
    postgres_user: str = "postgres"
    postgres_password: SecretStr = Field(default=SecretStr("postgres"))
    postgres_db: str = "app"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # CORS (adjust per microservice needs)
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Media uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance.

    Decision: lru_cache ensures we parse env only once per process.
    In tests, call get_settings.cache_clear() to reload.
    """
    return Settings()
