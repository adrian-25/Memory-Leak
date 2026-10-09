"""
Async SQLAlchemy 2.0 database engine and session factory.

Design:
- Engine is created once at startup from Settings.
- AsyncSession is provided per-request via FastAPI dependency injection.
- Repository classes receive an AsyncSession; they never access the engine directly.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Module-level engine and session factory — initialised at startup.
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """
    Create the async SQLAlchemy engine.

    Uses NullPool in test environments to avoid connection reuse issues.
    """
    settings = get_settings()
    url = database_url or settings.database_url

    connect_args: dict = {}
    pool_class = None

    if settings.app_env == "test":
        pool_class = NullPool

    kwargs: dict = {
        "echo": settings.app_debug,
        "future": True,
        "connect_args": connect_args,
    }
    if pool_class is not None:
        kwargs["poolclass"] = pool_class

    return create_async_engine(url, **kwargs)


def init_db(database_url: str | None = None) -> None:
    """
    Initialise the module-level engine and session factory.
    Must be called once during application startup.
    """
    global _engine, _async_session_factory

    _engine = create_engine(database_url)
    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    logger.info("database_engine_initialised", url=_engine.url.render_as_string(hide_password=True))


async def close_db() -> None:
    """Dispose the engine. Call during application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("database_engine_disposed")
        _engine = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a transactional AsyncSession per request.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() at startup.")

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_postgres_connection() -> dict[str, str]:
    """
    Verify PostgreSQL connectivity.
    Returns a status dict suitable for the /health endpoint.
    """
    if _engine is None:
        return {"status": "not_initialised"}

    try:
        from sqlalchemy import text
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        logger.warning("postgres_health_check_failed", error=str(exc))
        return {"status": "error", "detail": str(exc)}


async def check_pgvector_extension() -> dict[str, str]:
    """
    Verify that the pgvector extension is available in PostgreSQL.
    """
    if _engine is None:
        return {"status": "not_initialised"}

    try:
        import sqlalchemy

        async with _engine.connect() as conn:
            result = await conn.execute(
                sqlalchemy.text(
                    "SELECT extname FROM pg_extension WHERE extname = 'vector'"
                )
            )
            row = result.fetchone()
        if row:
            return {"status": "ok"}
        return {"status": "extension_not_installed"}
    except Exception as exc:
        logger.warning("pgvector_health_check_failed", error=str(exc))
        return {"status": "error", "detail": str(exc)}
