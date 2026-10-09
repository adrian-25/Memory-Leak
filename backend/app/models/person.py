"""
SQLAlchemy ORM model for the `people` table.

People are organizational members represented in knowledge and risk data.
They are synthetic in Phase 2; in later phases real data can be ingested.

People are DISTINCT from Users (platform operators).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Person(Base, TimestampMixin):
    __tablename__ = "people"
    __table_args__ = (
        Index("idx_people_org", "organization_id"),
        Index("idx_people_team", "team_id"),
    )

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
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    synthetic_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
        # Stable identifier from synthetic data generation
    )
    email_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True  # SHA-256 hash — never plain text
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    role_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="people"
    )
    team: Mapped["Team | None"] = relationship("Team", back_populates="members")
    expertise_scores: Mapped[list["ExpertiseScore"]] = relationship(
        "ExpertiseScore", back_populates="person"
    )

    def __repr__(self) -> str:
        return f"<Person id={self.id} name={self.display_name!r}>"
