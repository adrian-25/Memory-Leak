"""
Neo4j driver management for MemoryLeak backend.

Design:
- A single AsyncGraphDatabase driver is created at startup.
- Sessions are provided to callers via get_neo4j_session().
- The graph layer (app/intelligence/graph/) uses this client.

Note: Neo4j is a derived view. PostgreSQL is the system of record.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

_driver: AsyncDriver | None = None


def init_neo4j() -> None:
    """
    Initialise the module-level Neo4j async driver.
    Must be called once during application startup.
    """
    global _driver
    settings = get_settings()
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    logger.info("neo4j_driver_initialised", uri=settings.neo4j_uri)


async def close_neo4j() -> None:
    """Close the Neo4j driver. Call during application shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        logger.info("neo4j_driver_closed")
        _driver = None


async def get_neo4j_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a Neo4j AsyncSession per request.

    Usage:
        async def my_route(neo4j: AsyncSession = Depends(get_neo4j_session)):
            ...
    """
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised. Call init_neo4j() at startup.")

    async with _driver.session() as session:
        yield session


async def check_neo4j_connection() -> dict[str, str]:
    """
    Verify Neo4j connectivity.
    Returns a status dict suitable for the /health endpoint.
    """
    if _driver is None:
        return {"status": "not_initialised"}

    try:
        await _driver.verify_connectivity()
        return {"status": "ok"}
    except Exception as exc:
        logger.warning("neo4j_health_check_failed", error=str(exc))
        return {"status": "error", "detail": str(exc)}
