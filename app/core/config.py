from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Asset Management API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/asset_management",
        alias="DATABASE_URL",
    )
    database_migration_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/asset_management",
        alias="DATABASE_MIGRATION_URL",
    )
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_recycle_seconds: int = Field(default=1800, alias="DB_POOL_RECYCLE_SECONDS")

    cors_allowed_origins: list[str] = Field(default_factory=list, alias="CORS_ALLOWED_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    trusted_hosts: list[str] = Field(default_factory=list, alias="TRUSTED_HOSTS")

    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_minutes: int = Field(default=15, alias="JWT_ACCESS_TOKEN_MINUTES")
    jwt_refresh_token_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_DAYS")
    jwt_issuer: str = Field(default="asset-management-api", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="asset-management-client", alias="JWT_AUDIENCE")

    auth_bootstrap_admin_email: str | None = Field(
        default=None,
        alias="AUTH_BOOTSTRAP_ADMIN_EMAIL",
    )
    auth_bootstrap_admin_password: str | None = Field(
        default=None,
        alias="AUTH_BOOTSTRAP_ADMIN_PASSWORD",
    )
    auth_bootstrap_admin_full_name: str = Field(
        default="System Administrator",
        alias="AUTH_BOOTSTRAP_ADMIN_FULL_NAME",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
