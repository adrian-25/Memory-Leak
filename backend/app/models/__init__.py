"""
MemoryLeak ORM models — public package surface.

Import all models here so that:
1. SQLAlchemy's Base.metadata knows about every table.
2. Alembic's env.py can import Base and see all table definitions.
3. Application code can do: from app.models import Organization, User, ...

Ordering matters: models with FK dependencies must be imported AFTER their
referenced models. The order below respects the dependency graph.
"""
from __future__ import annotations

# ── Base and mixins ───────────────────────────────────────────────────────────
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# ── Core tables ───────────────────────────────────────────────────────────────
from app.models.organization import Organization
from app.models.user import User

# ── Domain entity tables (depend on Organization) ────────────────────────────
from app.models.team import Team
from app.models.person import Person         # depends on Team
from app.models.project import Project       # depends on Team
from app.models.service import Service       # depends on Project, Person
from app.models.knowledge_area import KnowledgeArea

# ── Ingestion tables ──────────────────────────────────────────────────────────
from app.models.raw_source import RawSource  # depends on Organization, User
from app.models.document import Document     # depends on RawSource, Person
from app.models.document_chunk import DocumentChunk  # depends on Document
from app.models.chunk_embedding import ChunkEmbedding  # depends on DocumentChunk

# ── Activity / event tables ───────────────────────────────────────────────────
from app.models.commit import Commit         # depends on Person, Service
from app.models.issue import Issue           # depends on Person, Service, Project
from app.models.discussion import Discussion  # depends on Person, self-ref

# ── Intelligence / scoring tables ────────────────────────────────────────────
from app.models.expertise_score import ExpertiseScore  # depends on Person, KnowledgeArea
from app.models.risk_score import RiskScore
from app.models.evidence_record import EvidenceRecord  # depends on DocumentChunk
from app.models.recommendation import Recommendation   # depends on RiskScore

# ── Audit / security tables ───────────────────────────────────────────────────
from app.models.audit_log import AuditLog    # depends on Organization, User

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # Core
    "Organization",
    "User",
    # Domain entities
    "Team",
    "Person",
    "Project",
    "Service",
    "KnowledgeArea",
    # Ingestion
    "RawSource",
    "Document",
    "DocumentChunk",
    "ChunkEmbedding",
    # Activity
    "Commit",
    "Issue",
    "Discussion",
    # Intelligence / scoring
    "ExpertiseScore",
    "RiskScore",
    "EvidenceRecord",
    "Recommendation",
    # Audit
    "AuditLog",
]
