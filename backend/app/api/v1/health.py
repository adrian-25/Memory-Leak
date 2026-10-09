"""
Health check endpoint.

GET /health — No authentication required.
Returns the live connectivity status of PostgreSQL, pgvector, and Neo4j.
Does NOT hardcode any dependency as healthy.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import check_pgvector_extension, check_postgres_connection
from app.core.neo4j_client import check_neo4j_connection
from app.schemas.health import HealthResponse, ServiceHealthStatus

router = APIRouter()

APP_VERSION = "0.1.0"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["system"],
)
async def health_check() -> HealthResponse:
    """
    Returns the health status of the MemoryLeak API and its dependencies.

    Checks:
    - PostgreSQL connectivity
    - pgvector extension availability
    - Neo4j connectivity

    The overall status is:
    - healthy: all dependencies OK
    - degraded: at least one dependency has an error
    - unhealthy: cannot determine state (initialisation failure)
    """
    settings = get_settings()

    # Run dependency checks sequentially.
    # asyncpg connections cannot be shared across concurrent asyncio tasks —
    # running them with asyncio.gather() causes "another operation in progress"
    # errors. Sequential checks are safe and fast enough for a health endpoint.
    postgres_result = await check_postgres_connection()
    pgvector_result = await check_pgvector_extension()
    neo4j_result = await check_neo4j_connection()

    services = {
        "postgres": ServiceHealthStatus(**postgres_result),
        "pgvector": ServiceHealthStatus(**pgvector_result),
        "neo4j": ServiceHealthStatus(**neo4j_result),
    }

    # Determine overall status
    all_ok = all(s.status == "ok" for s in services.values())
    any_error = any(s.status in ("error", "not_initialised") for s in services.values())

    if all_ok:
        overall = "healthy"
    elif any_error:
        overall = "degraded"
    else:
        overall = "degraded"

    return HealthResponse(
        status=overall,
        version=APP_VERSION,
        service="memoryleak-api",
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc),
        services=services,
    )
