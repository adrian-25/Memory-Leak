"""
SQLAlchemy ORM model for the `evidence_records` table.

Evidence records provide the provenance chain for every AI-generated claim,
risk score, or expertise measurement.

Every score and claim in MemoryLeak MUST have at least one EvidenceRecord.
This is a core design constraint — see docs/project-memory.md §Important Decisions.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        Index("idx_evidence_claim", "claim_type", "claim_id"),
        Index("idx_evidence_source", "source_type", "source_id"),
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
    claim_type: Mapped[str] = mapped_column(
        String(50), nullable=False
        # "expertise" | "risk" | "relationship"
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
        # FK to the relevant score/claim table — polymorphic
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
        # "document" | "commit" | "issue" | "graph_edge"
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )
    span_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    span_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    inference_type: Mapped[str] = mapped_column(
        String(20), nullable=False
        # "direct" | "inferred" | "aggregated"
    )
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<EvidenceRecord id={self.id} claim={self.claim_type}:{self.claim_id} "
            f"source={self.source_type}>"
        )
