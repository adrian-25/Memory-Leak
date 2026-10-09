"""
Unit tests for MemoryLeak ORM models.

These tests verify model structure, type annotations, and import correctness.
They do NOT require a running database — only the SQLAlchemy package.

Run with:
    pytest tests/unit/test_models.py -v

Or inside Docker:
    docker compose exec backend pytest tests/unit/test_models.py -v

Markers: @pytest.mark.unit
"""
from __future__ import annotations

import ast
import importlib
import inspect
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import get_type_hints

import pytest

pytestmark = pytest.mark.unit

# Path to the models package
MODELS_DIR = Path(__file__).parent.parent.parent / "app" / "models"

# All model files that define at least one table (not base.py or __init__.py)
MODEL_FILES = [
    "organization",
    "user",
    "team",
    "person",
    "project",
    "service",
    "knowledge_area",
    "raw_source",
    "document",
    "document_chunk",
    "chunk_embedding",
    "commit",
    "issue",
    "discussion",
    "expertise_score",
    "risk_score",
    "evidence_record",
    "recommendation",
    "audit_log",
]

# Expected table names in Base.metadata
EXPECTED_TABLES = {
    "organizations",
    "users",
    "teams",
    "people",
    "projects",
    "services",
    "knowledge_areas",
    "raw_sources",
    "documents",
    "document_chunks",
    "chunk_embeddings",
    "commits",
    "issues",
    "discussions",
    "expertise_scores",
    "risk_scores",
    "evidence_records",
    "recommendations",
    "audit_logs",
}

# Models exposed through __init__.py __all__
EXPECTED_EXPORTS = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "Organization",
    "User",
    "Team",
    "Person",
    "Project",
    "Service",
    "KnowledgeArea",
    "RawSource",
    "Document",
    "DocumentChunk",
    "ChunkEmbedding",
    "Commit",
    "Issue",
    "Discussion",
    "ExpertiseScore",
    "RiskScore",
    "EvidenceRecord",
    "Recommendation",
    "AuditLog",
]


# ─── Static AST checks (no imports needed) ────────────────────────────────────

class TestModelFilesSyntax:
    """Verify all model files have valid Python syntax via AST parsing."""

    @pytest.mark.parametrize("module_name", MODEL_FILES)
    def test_model_file_compiles(self, module_name: str):
        """Each model file must parse without syntax errors."""
        path = MODELS_DIR / f"{module_name}.py"
        assert path.exists(), f"Model file not found: {path}"
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {module_name}.py: {e}")

    def test_base_file_compiles(self):
        """base.py must parse without syntax errors."""
        path = MODELS_DIR / "base.py"
        source = path.read_text(encoding="utf-8")
        ast.parse(source)  # raises SyntaxError on failure

    def test_init_file_compiles(self):
        """__init__.py must parse without syntax errors."""
        path = MODELS_DIR / "__init__.py"
        source = path.read_text(encoding="utf-8")
        ast.parse(source)


class TestCreatedAtAnnotations:
    """
    Verify that models which define `created_at` manually use Mapped[datetime],
    not Mapped[uuid.UUID].

    This is a regression test for the bug found during Phase 1 audit:
    copy-paste error set created_at: Mapped[uuid.UUID] instead of Mapped[datetime].

    Uses AST parsing — no SQLAlchemy import required.
    """

    # Models that define created_at manually (do NOT use TimestampMixin)
    MANUAL_CREATED_AT_MODELS = [
        "team",
        "knowledge_area",
        "document_chunk",
        "chunk_embedding",
        "commit",
        "issue",
        "discussion",
        "evidence_record",
        "audit_log",
    ]

    @pytest.mark.parametrize("module_name", MANUAL_CREATED_AT_MODELS)
    def test_created_at_annotation_is_datetime_not_uuid(self, module_name: str):
        """
        created_at column must be Mapped[datetime], never Mapped[uuid.UUID].
        """
        path = MODELS_DIR / f"{module_name}.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Find every annotated assignment named 'created_at'
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign):
                # Get the target name
                if isinstance(node.target, ast.Name) and node.target.id == "created_at":
                    # Get the annotation as source text
                    annotation_src = ast.unparse(node.annotation)
                    assert "uuid.UUID" not in annotation_src, (
                        f"{module_name}.py: created_at annotation contains 'uuid.UUID'.\n"
                        f"Found: {annotation_src}\n"
                        f"Expected: Mapped[datetime]"
                    )
                    assert "datetime" in annotation_src, (
                        f"{module_name}.py: created_at annotation does not contain 'datetime'.\n"
                        f"Found: {annotation_src}\n"
                        f"Expected: Mapped[datetime]"
                    )

    def test_no_fragile_import_in_models(self):
        """
        No model file should use __import__("sqlalchemy") as a workaround.
        This was a bug in commit.py that has been fixed.
        """
        for module_name in MODEL_FILES:
            path = MODELS_DIR / f"{module_name}.py"
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if (
                        isinstance(node.func, ast.Name)
                        and node.func.id == "__import__"
                    ):
                        pytest.fail(
                            f"{module_name}.py uses __import__() at line {node.lineno}. "
                            "Use a proper top-level import instead."
                        )


class TestModelsInitExports:
    """Verify __init__.py exports all expected names."""

    def test_init_exports_all_expected_names(self):
        """
        __all__ in models/__init__.py must contain every expected model class.
        """
        path = MODELS_DIR / "__init__.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Find __all__ assignment
        all_names: list[str] = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(t, ast.Name) and t.id == "__all__"
                    for t in node.targets
                )
            ):
                if isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant):
                            all_names.append(elt.value)

        assert all_names, "models/__init__.py does not define __all__"

        for expected in EXPECTED_EXPORTS:
            assert expected in all_names, (
                f"models/__init__.py __all__ is missing: {expected!r}\n"
                f"Found: {sorted(all_names)}"
            )

    def test_init_imports_all_model_modules(self):
        """
        models/__init__.py must import from every model module.
        """
        path = MODELS_DIR / "__init__.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("app.models."):
                    module_name = node.module.split(".")[-1]
                    imported_modules.add(module_name)

        for model_file in MODEL_FILES:
            assert model_file in imported_modules, (
                f"models/__init__.py does not import from app.models.{model_file}"
            )


# ─── Import-level tests (require SQLAlchemy installed) ────────────────────────

class TestModelsImport:
    """
    Verify the full model import chain works and Base.metadata knows all tables.

    Requires: SQLAlchemy installed (available inside the Docker backend container).
    Skip if SQLAlchemy is not available (e.g., running on host without venv).
    """

    @pytest.fixture(autouse=True)
    def require_sqlalchemy(self):
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            pytest.skip("SQLAlchemy not installed — run inside Docker container")

    def test_all_models_importable_from_package(self):
        """from app.models import <AllModels> must succeed without error."""
        from app.models import (
            AuditLog,
            Base,
            ChunkEmbedding,
            Commit,
            Discussion,
            Document,
            DocumentChunk,
            EvidenceRecord,
            ExpertiseScore,
            KnowledgeArea,
            Organization,
            Person,
            Project,
            RawSource,
            Recommendation,
            RiskScore,
            Service,
            Team,
            TimestampMixin,
            UUIDPrimaryKeyMixin,
            User,
        )
        # If we reach here, the import chain is correct
        assert Organization is not None
        assert AuditLog is not None

    def test_base_metadata_contains_all_expected_tables(self):
        """Base.metadata must register all 19 domain tables."""
        from app.models import Base

        registered = set(Base.metadata.tables.keys())
        missing = EXPECTED_TABLES - registered
        assert not missing, (
            f"Base.metadata is missing tables: {sorted(missing)}\n"
            f"Registered tables: {sorted(registered)}"
        )

    def test_base_metadata_table_count(self):
        """Exactly 19 tables must be registered (no accidental duplicates)."""
        from app.models import Base

        registered = set(Base.metadata.tables.keys())
        assert len(registered) == len(EXPECTED_TABLES), (
            f"Expected {len(EXPECTED_TABLES)} tables, got {len(registered)}.\n"
            f"Tables: {sorted(registered)}"
        )

    @pytest.mark.parametrize("model_name,table_name", [
        ("Organization", "organizations"),
        ("User", "users"),
        ("Team", "teams"),
        ("Person", "people"),
        ("Project", "projects"),
        ("Service", "services"),
        ("KnowledgeArea", "knowledge_areas"),
        ("RawSource", "raw_sources"),
        ("Document", "documents"),
        ("DocumentChunk", "document_chunks"),
        ("ChunkEmbedding", "chunk_embeddings"),
        ("Commit", "commits"),
        ("Issue", "issues"),
        ("Discussion", "discussions"),
        ("ExpertiseScore", "expertise_scores"),
        ("RiskScore", "risk_scores"),
        ("EvidenceRecord", "evidence_records"),
        ("Recommendation", "recommendations"),
        ("AuditLog", "audit_logs"),
    ])
    def test_model_tablename(self, model_name: str, table_name: str):
        """Each ORM class must map to the correct table name."""
        import app.models as models_pkg
        model_cls = getattr(models_pkg, model_name)
        assert model_cls.__tablename__ == table_name, (
            f"{model_name}.__tablename__ = {model_cls.__tablename__!r}, "
            f"expected {table_name!r}"
        )

    def test_organization_has_uuid_primary_key(self):
        """Organization.id must be a UUID column."""
        from app.models import Organization
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID
        col = Organization.__table__.c["id"]
        assert isinstance(col.type, PG_UUID), (
            f"Organization.id type is {type(col.type)}, expected UUID"
        )

    def test_all_tables_have_id_column(self):
        """Every table must have an 'id' primary key column."""
        from app.models import Base
        for table_name, table in Base.metadata.tables.items():
            assert "id" in table.c, (
                f"Table {table_name!r} has no 'id' column"
            )
            pk_cols = [c.name for c in table.primary_key.columns]
            assert "id" in pk_cols, (
                f"Table {table_name!r} 'id' column is not a primary key"
            )
