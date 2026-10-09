"""
SQLAlchemy ORM model for the `chunk_embeddings` table.

Stores the dense vector embedding for each DocumentChunk.
Uses the pgvector VECTOR column type for semantic search.

NOTE: The IVFFlat index (for ANN search) is intentionally NOT created here.
It must be created after bulk data load — see data-model.md §4.3.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

try:
    from pgvector.sqlalchemy import Vector  # pgvector SQLAlchemy integration

    _VECTOR_TYPE = Vector(384)
except ImportError:
    # pgvector package not installed yet (Phase 4 will install it fully).
    # Fall back to a plain Text column so Alembic can still import models.
    from sqlalchemy import Text as _VECTOR_FALLBACK  # type: ignore[assignment]

    _VECTOR_TYPE = None  # type: ignore[assignment]


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"
    __table_args__ = (Index("idx_embeddings_org", "organization_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # embedding stored as VECTOR(384) via pgvector — native VECTOR DDL via migration
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    chunk: Mapped["DocumentChunk"] = relationship(
        "DocumentChunk", back_populates="embedding"
    )

    def __repr__(self) -> str:
        return f"<ChunkEmbedding id={self.id} chunk={self.chunk_id} model={self.model_name!r}>"
