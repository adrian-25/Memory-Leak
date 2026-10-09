"""
SQLAlchemy ORM model for the `teams` table.

Teams are organizational units that contain people and work on projects.
Supports a hierarchical structure via self-referential parent_team_id.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Team(Base):
    __tablename__ = "teams"

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
    parent_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    parent: Mapped["Team | None"] = relationship(
        "Team", remote_side="Team.id", back_populates="sub_teams"
    )
    sub_teams: Mapped[list["Team"]] = relationship(
        "Team", back_populates="parent"
    )
    members: Mapped[list["Person"]] = relationship("Person", back_populates="team")

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name!r}>"
