"""
Pytest configuration and fixtures for MemoryLeak backend tests.

Phase 1: fixtures for the FastAPI test client.
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Point at a test .env if one exists; otherwise rely on environment variables.
os.environ.setdefault("APP_ENV", "test")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def client():
    """
    Provides an httpx AsyncClient that speaks directly to the FastAPI app
    (no network socket needed).

    The app's lifespan is invoked, which means real database connections
    are established. The test database must be running.
    """
    from app.main import create_app

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
