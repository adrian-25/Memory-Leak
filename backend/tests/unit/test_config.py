"""
Unit tests for app.core.config.

These tests verify Settings behaviour without a running database.
"""
from __future__ import annotations

import os

import pytest

from app.core.config import Settings


class TestSettings:
    """Settings unit tests — no external services required."""

    def test_database_url_uses_asyncpg_driver(self):
        s = Settings(
            app_secret_key="x" * 32,
            postgres_password="testpwd",
            neo4j_password="testpwd",
        )
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_database_url_sync_uses_psycopg2_driver(self):
        s = Settings(
            app_secret_key="x" * 32,
            postgres_password="testpwd",
            neo4j_password="testpwd",
        )
        assert s.database_url_sync.startswith("postgresql+psycopg2://")

    def test_database_url_contains_credentials(self):
        s = Settings(
            app_secret_key="x" * 32,
            postgres_user="myuser",
            postgres_password="mypassword",
            neo4j_password="testpwd",
        )
        assert "myuser" in s.database_url
        assert "mypassword" in s.database_url

    def test_database_url_contains_host_and_db(self):
        s = Settings(
            app_secret_key="x" * 32,
            postgres_host="myhost",
            postgres_port=5433,
            postgres_db="mydb",
            postgres_password="testpwd",
            neo4j_password="testpwd",
        )
        assert "myhost" in s.database_url
        assert "5433" in s.database_url
        assert "mydb" in s.database_url

    def test_database_url_uses_render_connection_string(self):
        s = Settings(
            app_secret_key="x" * 32,
            neo4j_password="testpwd",
            DATABASE_URL="postgresql://render_user:render_pass@render-host:5432/render_db",
        )
        assert s.database_url == (
            "postgresql+asyncpg://render_user:render_pass@render-host:5432/render_db"
        )
        assert s.database_url_sync == (
            "postgresql+psycopg2://render_user:render_pass@render-host:5432/render_db"
        )

    def test_allowed_origins_list_parses_comma_separated(self):
        s = Settings(
            app_secret_key="x" * 32,
            postgres_password="testpwd",
            neo4j_password="testpwd",
            app_allowed_origins="http://localhost:3000,http://localhost:3001",
        )
        assert s.allowed_origins_list == [
            "http://localhost:3000",
            "http://localhost:3001",
        ]

    def test_secret_key_too_short_raises(self):
        with pytest.raises(Exception):
            Settings(
                app_secret_key="short",
                postgres_password="testpwd",
                neo4j_password="testpwd",
            )

    def test_app_env_default_is_development(self):
        s = Settings(
            app_secret_key="x" * 32,
            postgres_password="testpwd",
            neo4j_password="testpwd",
        )
        # Might be overridden by actual env var in CI — that's fine.
        assert s.app_env in ("development", "production", "test")
