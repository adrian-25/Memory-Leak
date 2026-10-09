"""
SQLAlchemy ORM model for the `commits` table.

Commits are ingested from version control history.
They are the primary evidence source for expertise scoring.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Commit(Base):
    __tablename__ = "commits"
    __table_args__ = (
        Index("idx_commits_author", "author_id"),
        Index("idx_commits_service", "service_id"),
        Index("idx_commits_date", "committed_at"),
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
    external_id: Mapped[str] = mapped_column(
        String(255), nullable=False  # original commit hash / ID
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    files_changed: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    additions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deletions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    committed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Commit id={self.id} ext={self.external_id!r}>"
