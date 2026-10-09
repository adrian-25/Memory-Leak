"""
SQLAlchemy ORM model for the `services` table.

Services are deployed software components — microservices, APIs, libraries, etc.
They are the primary unit of bus-factor and knowledge concentration risk.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Service(Base, TimestampMixin):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    criticality: Mapped[str | None] = mapped_column(
        String(20), nullable=True  # "critical" | "high" | "medium" | "low"
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    primary_owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
    )
    repository_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    project: Mapped["Project | None"] = relationship(
        "Project", back_populates="services"
    )
    primary_owner: Mapped["Person | None"] = relationship(
        "Person", foreign_keys=[primary_owner_id]
    )

    def __repr__(self) -> str:
        return f"<Service id={self.id} name={self.name!r} criticality={self.criticality!r}>"
