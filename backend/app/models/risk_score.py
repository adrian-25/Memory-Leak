"""
SQLAlchemy ORM model for the `risk_scores` table.

Stores pre-computed risk scores per entity. Every risk score must be backed
by evidence — no score without a traceable evidence chain.

IMPORTANT: Risk scores must not be used for employment decisions.
See docs/limitations.md and docs/architecture.md §6.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"
    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "risk_category",
            name="uq_risk_entity_category"
        ),
        Index("idx_risk_entity", "entity_type", "entity_id"),
        Index("idx_risk_severity", "severity"),
        Index("idx_risk_category", "risk_category"),
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
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
        # "person" | "service" | "project" | "knowledge_area" | "organization"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
        # Polymorphic FK — no DB-level referential integrity by design
    )
    risk_category: Mapped[str] = mapped_column(
        String(50), nullable=False
        # "bus_factor" | "knowledge_concentration" | "documentation_coverage"
        # | "documentation_staleness" | "doc_code_drift"
        # | "dependency_risk" | "overall"
    )
    score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
        # "critical" | "high" | "medium" | "low" | "info"
    )
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    contributing_factors: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<RiskScore entity={self.entity_type}:{self.entity_id} "
            f"category={self.risk_category!r} score={self.score} severity={self.severity!r}>"
        )
