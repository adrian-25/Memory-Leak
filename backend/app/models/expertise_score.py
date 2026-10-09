"""
SQLAlchemy ORM model for the `expertise_scores` table.

Stores the computed expertise score for each (person, knowledge_area) pair.
Each row is a pre-computed, evidence-backed measurement.

IMPORTANT: Scores are evidence-based proxies, NOT direct knowledge measurements.
See docs/limitations.md LIM-TECH-06.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ExpertiseScore(Base):
    __tablename__ = "expertise_scores"
    __table_args__ = (
        UniqueConstraint(
            "person_id", "knowledge_area_id", name="uq_expertise_person_area"
        ),
        Index("idx_expertise_person", "person_id"),
        Index("idx_expertise_area", "knowledge_area_id"),
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
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
    )
    knowledge_area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_areas.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False  # 0.0000 – 1.0000
    )
    recency_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    breadth_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    depth_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    person: Mapped["Person"] = relationship("Person", back_populates="expertise_scores")
    knowledge_area: Mapped["KnowledgeArea"] = relationship(
        "KnowledgeArea", back_populates="expertise_scores"
    )

    def __repr__(self) -> str:
        return (
            f"<ExpertiseScore person={self.person_id} "
            f"area={self.knowledge_area_id} score={self.score}>"
        )
