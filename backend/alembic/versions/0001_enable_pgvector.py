"""Enable pgvector extension

Revision ID: 0001_enable_pgvector
Revises: 
Create Date: 2026-09-03 20:00:00.000000+00:00

This is the initial migration.
It enables the pgvector extension required for chunk embeddings.

The full domain schema (organizations, users, documents, etc.) is
implemented in Phase 1 migration 0002 and expanded in later phases.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0001_enable_pgvector"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector — required for VECTOR column type used in chunk_embeddings.
    # This is idempotent: IF NOT EXISTS prevents failure if already enabled.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Note: dropping the vector extension will fail if any VECTOR columns exist.
    # This is intentional — the extension cannot be safely removed if in use.
    op.execute("DROP EXTENSION IF EXISTS vector")
