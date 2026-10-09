"""
Integration tests — Phase 1 connectivity smoke tests.

These tests require a running Docker stack (postgres, neo4j).
Run with: docker compose exec backend pytest tests/integration/ -v

Markers: @pytest.mark.integration

DESIGN:
Two test strategies are used:

1. Live HTTP tests (TestLiveHealthEndpoint):
   Call the REAL running server at http://localhost:8000 via httpx.
   These are the authoritative end-to-end tests. They require the server
   to be running (which it is when this file runs inside the container,
   because the backend service starts before tests execute).

2. Direct module tests (TestPostgresConnectivity, TestNeo4jConnectivity):
   Call core module functions directly to verify DB/graph connectivity.
   Authoritative smoke tests for Phase 1.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
import httpx


pytestmark = pytest.mark.integration

# Base URL of the live server — inside the Docker container this resolves to self
LIVE_BASE_URL = "http://localhost:8000"


# ─── Live HTTP tests against the running server ────────────────────────────────

class TestLiveHealthEndpoint:
    """
    Call the REAL running FastAPI server via HTTP.
    These tests do NOT use ASGI transport — they hit the live server.
    This avoids all event loop isolation issues.
    """

    async def test_health_returns_200(self):
        """GET /health must return HTTP 200."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            response = await client.get("/health")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Body: {response.text}"
        )

    async def test_health_response_structure(self):
        """Response must contain all required fields."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            body = (await client.get("/health")).json()
        assert "status" in body
        assert "version" in body
        assert "service" in body
        assert "services" in body
        assert body["service"] == "memoryleak-api"
        assert body["version"] == "0.1.0"

    async def test_health_contains_all_service_checks(self):
        """Response must include postgres, pgvector, and neo4j entries."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            body = (await client.get("/health")).json()
        services = body["services"]
        assert "postgres" in services
        assert "pgvector" in services
        assert "neo4j" in services

    async def test_postgres_reports_ok(self):
        """PostgreSQL must report ok."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            body = (await client.get("/health")).json()
        assert body["services"]["postgres"]["status"] == "ok", (
            f"PostgreSQL not ok: {body['services']['postgres']}"
        )

    async def test_pgvector_reports_ok(self):
        """pgvector extension must be installed and report ok."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            body = (await client.get("/health")).json()
        assert body["services"]["pgvector"]["status"] == "ok", (
            f"pgvector not ok: {body['services']['pgvector']}. "
            "Ensure migration applied: docker compose exec backend alembic upgrade head"
        )

    async def test_neo4j_reports_ok(self):
        """Neo4j must report ok."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            body = (await client.get("/health")).json()
        assert body["services"]["neo4j"]["status"] == "ok", (
            f"Neo4j not ok: {body['services']['neo4j']}"
        )

    async def test_overall_status_is_healthy(self):
        """Overall status must be 'healthy' when all deps are ok."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            body = (await client.get("/health")).json()
        assert body["status"] == "healthy", (
            f"Expected status=healthy, got {body['status']}. Full body: {body}"
        )

    async def test_health_timestamp_is_present(self):
        """Timestamp must be present and non-empty."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            body = (await client.get("/health")).json()
        assert "timestamp" in body
        assert len(body["timestamp"]) > 10

    async def test_docs_endpoint_accessible(self):
        """FastAPI /docs must be accessible in development mode."""
        async with httpx.AsyncClient(base_url=LIVE_BASE_URL, timeout=10.0) as client:
            response = await client.get("/docs")
        assert response.status_code == 200, (
            f"Expected /docs to be accessible, got {response.status_code}"
        )


# ─── Direct database connectivity (module-level smoke tests) ───────────────────

class TestPostgresConnectivity:
    """
    Directly verify PostgreSQL + pgvector connectivity via core module.
    """

    async def test_postgres_direct_connection(self):
        """PostgreSQL must be reachable and accept queries."""
        from app.core.database import check_postgres_connection, init_db
        init_db()
        result = await check_postgres_connection()
        assert result["status"] == "ok", f"Direct postgres check failed: {result}"

    async def test_pgvector_extension_via_direct_connection(self):
        """pgvector extension must be installed (migration 0001 applied)."""
        from app.core.database import check_pgvector_extension, init_db
        init_db()
        result = await check_pgvector_extension()
        assert result["status"] == "ok", (
            f"pgvector extension not installed: {result}. "
            "Run: docker compose exec backend alembic upgrade head"
        )


class TestNeo4jConnectivity:
    """
    Directly verify Neo4j connectivity via core module.
    """

    async def test_neo4j_direct_connection(self):
        """Neo4j must be reachable and accept driver verification."""
        from app.core.neo4j_client import check_neo4j_connection, init_neo4j
        init_neo4j()
        result = await check_neo4j_connection()
        assert result["status"] == "ok", f"Direct neo4j check failed: {result}"
