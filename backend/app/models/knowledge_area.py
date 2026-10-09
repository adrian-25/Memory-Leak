"""
SQLAlchemy ORM model for the `knowledge_areas` table.

Knowledge areas are named domains of expertise — "authentication", "payments",
"data pipelines", etc. They form the basis of expertise scoring and risk analysis.
Supports a hierarchical structure via self-referential parent_area_id.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class KnowledgeArea(Base):
    __tablename__ = "knowledge_areas"

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
    category: Mapped[str | None] = mapped_column(
        Text, nullable=True  # e.g. "technology", "domain", "process"
    )
    parent_area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_areas.id", ondelete="SET NULL"),
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
    parent: Mapped["KnowledgeArea | None"] = relationship(
        "KnowledgeArea",
        remote_side="KnowledgeArea.id",
        back_populates="children",
    )
    children: Mapped[list["KnowledgeArea"]] = relationship(
        "KnowledgeArea", back_populates="parent"
    )
    expertise_scores: Mapped[list["ExpertiseScore"]] = relationship(
        "ExpertiseScore", back_populates="knowledge_area"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeArea id={self.id} name={self.name!r}>"
