"""Create core domain tables

Revision ID: 0002_create_core_tables
Revises: 0001_enable_pgvector
Create Date: 2026-09-05 07:00:00.000000+00:00

Creates all Phase 1 core tables in dependency order:

  Core:        organizations, users
  Entities:    teams, people, projects, services, knowledge_areas
  Ingestion:   raw_sources, documents, document_chunks, chunk_embeddings
  Activity:    commits, issues, discussions
  Intelligence: expertise_scores, risk_scores, evidence_records, recommendations
  Audit:       audit_logs

The pgvector extension must already be enabled (migration 0001).

The chunk_embeddings.embedding VECTOR(384) column is created via raw SQL because
the SQLAlchemy pgvector type requires the pgvector Python package at import time.
The DDL itself works as long as the pg extension is present (ensured by 0001).

IVFFlat index on chunk_embeddings.embedding is NOT created here — it must be
created after bulk data load (see docs/data-model.md §4.3).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_create_core_tables"
down_revision: Union[str, None] = "0001_enable_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── organizations ─────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
        sa.CheckConstraint("role IN ('admin', 'analyst', 'viewer')", name="ck_users_role"),
    )

    # ── teams ─────────────────────────────────────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("parent_team_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )

    # ── people ────────────────────────────────────────────────────────────────
    op.create_table(
        "people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("synthetic_id", sa.String(255), unique=True, nullable=False),
        sa.Column("email_hash", sa.String(64), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("role_title", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_people_org", "people", ["organization_id"])
    op.create_index("idx_people_team", "people", ["team_id"])

    # ── projects ──────────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'archived')", name="ck_projects_status"
        ),
    )

    # ── services ──────────────────────────────────────────────────────────────
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("criticality", sa.String(20), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("primary_owner_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("repository_url", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "criticality IN ('critical', 'high', 'medium', 'low')",
            name="ck_services_criticality",
        ),
    )

    # ── knowledge_areas ───────────────────────────────────────────────────────
    op.create_table(
        "knowledge_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.Text, nullable=True),
        sa.Column("parent_area_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_areas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )

    # ── raw_sources ───────────────────────────────────────────────────────────
    op.create_table(
        "raw_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("file_name", sa.Text, nullable=False),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default=sa.text("'pending'")),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("ingested_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "content_hash", name="uq_raw_sources_hash_org"
        ),
        sa.CheckConstraint(
            "source_type IN ('pdf','docx','markdown','txt','python','javascript',"
            "'typescript','java','sql','yaml','json','toml','ini',"
            "'issues','commits','discussions')",
            name="ck_raw_sources_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending','processing','completed','failed')",
            name="ck_raw_sources_status",
        ),
    )
    op.create_index("idx_raw_sources_org", "raw_sources", ["organization_id"])
    op.create_index("idx_raw_sources_status", "raw_sources", ["status"])

    # ── documents ─────────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_source_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("raw_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("author_name", sa.Text, nullable=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("authored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("word_count", sa.Integer, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_documents_org", "documents", ["organization_id"])
    op.create_index("idx_documents_author", "documents", ["author_id"])
    op.create_index("idx_documents_type", "documents", ["document_type"])

    # ── document_chunks ───────────────────────────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("start_char", sa.Integer, nullable=True),
        sa.Column("end_char", sa.Integer, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_chunks_document", "document_chunks", ["document_id"])
    op.create_index("idx_chunks_org", "document_chunks", ["organization_id"])

    # ── chunk_embeddings ──────────────────────────────────────────────────────
    # embedding column uses native VECTOR(384) DDL (pgvector must be enabled).
    # We use raw SQL for the column because SQLAlchemy's pgvector type requires
    # the pgvector Python package at import time, which is installed in Phase 4.
    op.create_table(
        "chunk_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("document_chunks.id", ondelete="CASCADE"),
                  unique=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    # Add the VECTOR column via raw DDL (pgvector extension must be enabled)
    op.execute(
        "ALTER TABLE chunk_embeddings ADD COLUMN embedding vector(384)"
    )
    op.create_index("idx_embeddings_org", "chunk_embeddings", ["organization_id"])
    # NOTE: IVFFlat ANN index is NOT created here.
    # Create it after bulk data load:
    #   CREATE INDEX idx_embeddings_vector ON chunk_embeddings
    #       USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

    # ── commits ───────────────────────────────────────────────────────────────
    op.create_table(
        "commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("files_changed", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("additions", sa.Integer, nullable=True),
        sa.Column("deletions", sa.Integer, nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_commits_author", "commits", ["author_id"])
    op.create_index("idx_commits_service", "commits", ["service_id"])
    op.create_index("idx_commits_date", "commits", ["committed_at"])

    # ── issues ────────────────────────────────────────────────────────────────
    op.create_table(
        "issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolver_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at_ext", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at_ext", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )

    # ── discussions ───────────────────────────────────────────────────────────
    op.create_table(
        "discussions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.Text, nullable=False),
        sa.Column("thread_id", sa.Text, nullable=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("discussions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at_ext", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )

    # ── expertise_scores ──────────────────────────────────────────────────────
    op.create_table(
        "expertise_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="CASCADE"), nullable=False),
        sa.Column("knowledge_area_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("knowledge_areas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("recency_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("breadth_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("depth_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint(
            "person_id", "knowledge_area_id", name="uq_expertise_person_area"
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 1", name="ck_expertise_score_range"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_expertise_confidence_range"),
    )
    op.create_index("idx_expertise_person", "expertise_scores", ["person_id"])
    op.create_index("idx_expertise_area", "expertise_scores", ["knowledge_area_id"])

    # ── risk_scores ───────────────────────────────────────────────────────────
    op.create_table(
        "risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_category", sa.String(50), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("contributing_factors", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("limitations", sa.Text, nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint(
            "entity_type", "entity_id", "risk_category",
            name="uq_risk_entity_category",
        ),
        sa.CheckConstraint(
            "entity_type IN ('person','service','project','knowledge_area','organization')",
            name="ck_risk_entity_type",
        ),
        sa.CheckConstraint(
            "risk_category IN ('bus_factor','knowledge_concentration',"
            "'documentation_coverage','documentation_staleness',"
            "'doc_code_drift','dependency_risk','overall')",
            name="ck_risk_category",
        ),
        sa.CheckConstraint(
            "severity IN ('critical','high','medium','low','info')",
            name="ck_risk_severity",
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 1", name="ck_risk_score_range"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_risk_confidence_range"),
    )
    op.create_index("idx_risk_entity", "risk_scores", ["entity_type", "entity_id"])
    op.create_index("idx_risk_severity", "risk_scores", ["severity"])
    op.create_index("idx_risk_category", "risk_scores", ["risk_category"])

    # ── evidence_records ──────────────────────────────────────────────────────
    op.create_table(
        "evidence_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_type", sa.String(50), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("span_start", sa.Integer, nullable=True),
        sa.Column("span_end", sa.Integer, nullable=True),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("inference_type", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "inference_type IN ('direct','inferred','aggregated')",
            name="ck_evidence_inference_type",
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1", name="ck_evidence_confidence_range"
        ),
    )
    op.create_index("idx_evidence_claim", "evidence_records", ["claim_type", "claim_id"])
    op.create_index("idx_evidence_source", "evidence_records", ["source_type", "source_id"])

    # ── recommendations ───────────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_type", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("target_entity_type", sa.Text, nullable=True),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("risk_score_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("risk_scores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
                  nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(20), nullable=False, server_default="'open'"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "recommendation_type IN ('document_gap','backup_expert',"
            "'knowledge_transfer','risk_mitigation')",
            name="ck_rec_type",
        ),
        sa.CheckConstraint(
            "priority IN ('critical','high','medium','low')", name="ck_rec_priority"
        ),
        sa.CheckConstraint(
            "status IN ('open','in_progress','resolved','dismissed')", name="ck_rec_status"
        ),
    )

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "operation IN ('create','read','update','delete','export')",
            name="ck_audit_operation",
        ),
    )
    op.create_index("idx_audit_org", "audit_logs", ["organization_id"])
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_time", "audit_logs", ["created_at"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("audit_logs")
    op.drop_table("recommendations")
    op.drop_table("evidence_records")
    op.drop_table("risk_scores")
    op.drop_table("expertise_scores")
    op.drop_table("discussions")
    op.drop_table("issues")
    op.drop_table("commits")
    op.drop_table("chunk_embeddings")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("raw_sources")
    op.drop_table("knowledge_areas")
    op.drop_table("services")
    op.drop_table("projects")
    op.drop_table("people")
    op.drop_table("teams")
    op.drop_table("users")
    op.drop_table("organizations")
