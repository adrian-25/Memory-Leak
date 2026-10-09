"""
Application configuration — reads from environment variables / .env file.
All secrets are loaded from the environment; nothing is hardcoded here.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_env: Literal["development", "production", "test"] = "development"
    app_debug: bool = False
    app_secret_key: str = Field(..., min_length=32)
    app_allowed_origins: str = "http://localhost:3000"

    # ── JWT ────────────────────────────────────────────────────────────────────
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ── PostgreSQL ─────────────────────────────────────────────────────────────
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "memoryleak"
    postgres_user: str = "memoryleak_user"
    postgres_password: str | None = Field(default=None, min_length=1)

    # Managed platforms such as Render provide a single Postgres connection
    # string.  Keep the individual settings for local Docker Compose, while
    # allowing production to supply that connection string directly.
    postgres_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    # ── Neo4j ──────────────────────────────────────────────────────────────────
    # Neo4j is a derived view rather than the system of record. It is
    # optional in hosted starter deployments and can be connected later.
    neo4j_uri: str | None = None
    neo4j_user: str | None = None
    neo4j_password: str | None = Field(default=None, min_length=1)

    # ── Embeddings ─────────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 64

    # ── NLP ────────────────────────────────────────────────────────────────────
    spacy_model: str = "en_core_web_sm"

    # ── Synthetic Data ─────────────────────────────────────────────────────────
    random_seed: int = 42

    # ── Observability ──────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # ── Computed fields ────────────────────────────────────────────────────────
    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """Async URL used by SQLAlchemy (asyncpg driver)."""
        if self.postgres_url:
            return self._with_database_driver("postgresql+asyncpg")
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def database_url_sync(self) -> str:
        """Sync URL used by Alembic (psycopg2 driver)."""
        if self.postgres_url:
            return self._with_database_driver("postgresql+psycopg2")
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_allowed_origins.split(",")]

    def _with_database_driver(self, driver: str) -> str:
        """Adapt a standard Render Postgres URL for the required SQLAlchemy driver."""
        assert self.postgres_url is not None
        if self.postgres_url.startswith("postgresql://"):
            return self.postgres_url.replace("postgresql://", f"{driver}://", 1)
        if self.postgres_url.startswith("postgres://"):
            return self.postgres_url.replace("postgres://", f"{driver}://", 1)
        return self.postgres_url

    @model_validator(mode="after")
    def validate_database_configuration(self) -> "Settings":
        """Accept either Render's complete URL or local Compose credentials."""
        if not self.postgres_url and not self.postgres_password:
            raise ValueError("POSTGRES_PASSWORD is required when DATABASE_URL is not set")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings. Use as a FastAPI dependency."""
    return Settings()  # type: ignore[call-arg]
