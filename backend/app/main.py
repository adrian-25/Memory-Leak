"""
MemoryLeak — FastAPI application entrypoint.

This module creates the FastAPI app, registers routers, and manages the
lifespan (startup/shutdown) of database connections.

Phase 1: /health endpoint + database connectivity.
Future phases will add ingestion, intelligence, and other routers here.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.dashboard import router as dashboard_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.logging import configure_logging, get_logger
from app.core.neo4j_client import close_neo4j, init_neo4j

# ─── Startup/Shutdown lifecycle ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle: initialise connections on startup,
    dispose them on shutdown.
    """
    settings = get_settings()

    # Configure logging first so all subsequent messages are structured.
    configure_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    logger = get_logger(__name__)

    logger.info(
        "memoryleak_starting",
        environment=settings.app_env,
        version="0.1.0",
    )

    # Initialise PostgreSQL connection pool
    try:
        init_db()
        logger.info("postgres_connection_pool_ready")
    except Exception as exc:
        logger.error("postgres_init_failed", error=str(exc))
        raise

    # Initialise Neo4j driver
    try:
        init_neo4j()
        logger.info("neo4j_driver_ready")
    except Exception as exc:
        logger.error("neo4j_init_failed", error=str(exc))
        raise

    logger.info("memoryleak_startup_complete")

    yield  # ← application runs here

    # Shutdown
    logger.info("memoryleak_shutting_down")
    await close_db()
    await close_neo4j()
    logger.info("memoryleak_shutdown_complete")


# ─── Application factory ──────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="MemoryLeak API",
        description=(
            "AI-Powered Organizational Knowledge Risk and Dependency Intelligence Platform. "
            "Phase 1 — Infrastructure."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # CORS — allows the Next.js frontend on port 3000 to call the API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────────
    # Health check is mounted at root (not under /api/v1) for easy access.
    app.include_router(health_router)
    app.include_router(dashboard_router)

    # Phase 1 placeholder: future routers are registered here in later phases.
    # app.include_router(ingestion_router, prefix="/api/v1")
    # app.include_router(knowledge_router, prefix="/api/v1")
    # app.include_router(risks_router, prefix="/api/v1")
    # ... (see docs/api-specification.md for full list)

    return app


# ─── WSGI/ASGI entrypoint ─────────────────────────────────────────────────────

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
