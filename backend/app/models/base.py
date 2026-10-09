"""
SQLAlchemy 2.0 declarative base for all ORM models.

All domain models inherit from Base. This module also provides
the TimestampMixin used across most tables.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all MemoryLeak ORM models."""
    pass


class TimestampMixin:
    """
    Adds created_at and updated_at columns to any model.

    Both columns are timezone-aware and default to the current UTC time.
    updated_at is automatically refreshed on every row update via onupdate.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column to any model."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
