"""
SQLAlchemy ORM model for the `discussions` table.

Discussions are threaded conversations from Slack, GitHub Discussions,
team forums, etc. They provide informal evidence of knowledge and expertise.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Discussion(Base):
    __tablename__ = "discussions"

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
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    thread_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discussions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at_ext: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    parent: Mapped["Discussion | None"] = relationship(
        "Discussion", remote_side="Discussion.id", back_populates="replies"
    )
    replies: Mapped[list["Discussion"]] = relationship(
        "Discussion", back_populates="parent"
    )

    def __repr__(self) -> str:
        return f"<Discussion id={self.id} thread={self.thread_id!r}>"
