"""
SQLAlchemy ORM model for the `raw_sources` table.

Tracks every uploaded or ingested source file or data feed.
One RawSource produces one or more Documents after parsing.
"""
from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RawSource(Base, TimestampMixin):
    __tablename__ = "raw_sources"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "content_hash", name="uq_raw_sources_hash_org"
        ),
        Index("idx_raw_sources_org", "organization_id"),
        Index("idx_raw_sources_status", "status"),
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
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False  # SHA-256 hex
    )
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
        # "pending" | "processing" | "completed" | "failed"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="raw_sources"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="raw_source"
    )

    def __repr__(self) -> str:
        return f"<RawSource id={self.id} file={self.file_name!r} status={self.status!r}>"
