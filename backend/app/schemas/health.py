"""Pydantic schemas for the /health endpoint."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ServiceHealthStatus(BaseModel):
    """Health status of a single downstream service."""

    status: Literal["ok", "error", "not_initialised", "extension_not_installed"]
    detail: str | None = None


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    service: str
    environment: str
    timestamp: datetime
    services: dict[str, ServiceHealthStatus]
