"""
SQLAlchemy ORM model for the `organizations` table.

An Organization is the top-level tenant. All other entities belong to an organization.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships (back-populated from child models) ──────────────────────
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    raw_sources: Mapped[list["RawSource"]] = relationship(
        "RawSource", back_populates="organization"
    )
    people: Mapped[list["Person"]] = relationship("Person", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug!r}>"
