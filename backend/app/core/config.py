"""Application configuration, loaded from environment variables."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. All values are overridable via ``TRACELINK_*`` env vars."""

    model_config = SettingsConfigDict(env_prefix="TRACELINK_", env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://tracelink:tracelink@localhost:5432/tracelink",
        description="SQLAlchemy database URL (psycopg v3 driver).",
    )
    cors_origins: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed CORS origins.",
    )
    # Default identity used until the pluggable auth layer lands (see roadmap).
    current_user: str = Field(default="Clara Martin", description="Single local user name.")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
