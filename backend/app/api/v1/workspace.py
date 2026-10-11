"""Authenticated-ready workspace ingestion endpoints.

The starter deployment has no identity provider configured yet, so the routes
accept an explicit organization slug.  The data model remains organization
scoped and can be protected by the future RBAC dependency without changing
the API payloads.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models import Organization
from app.services.workspace import get_or_create_organization, ingest_text, recompute_workspace

router = APIRouter(prefix="/api/v1", tags=["workspace"])

SourceType = Literal["document", "code", "issue", "discussion", "config"]


class IngestTextRequest(BaseModel):
    organization_slug: str = Field(default="default", min_length=1, max_length=100)
    organization_name: str = Field(default="My workspace", min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=100_000)
    source_type: SourceType = "document"
    file_name: str = Field(default="evidence.txt", min_length=1, max_length=500)
    author_name: str | None = Field(default=None, max_length=255)
    service_name: str | None = Field(default=None, max_length=255)
    knowledge_areas: list[str] = Field(default_factory=list, max_length=20)
    last_modified: datetime | None = None


class BulkIngestRequest(BaseModel):
    records: list[IngestTextRequest] = Field(min_length=1, max_length=100)


def _upload_text(upload: UploadFile, data: bytes) -> str:
    """Extract text from a safe, bounded set of workspace evidence formats."""
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            from io import BytesIO
            return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
        except Exception as exc:  # parsing error should be actionable, not silent
            raise ValueError(f"Could not read PDF: {exc}") from exc
    if suffix == ".docx":
        try:
            from docx import Document
            from io import BytesIO
            return "\n".join(paragraph.text for paragraph in Document(BytesIO(data)).paragraphs)
        except Exception as exc:
            raise ValueError(f"Could not read DOCX: {exc}") from exc
    if suffix in {".txt", ".md", ".py", ".js", ".ts", ".java", ".sql", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"}:
        return data.decode("utf-8", errors="replace")
    raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT, Markdown, code, JSON, YAML, TOML, or INI.")


async def _persist(request: IngestTextRequest, session: AsyncSession) -> dict:
    try:
        return await ingest_text(session, **request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/workspaces")
async def list_workspaces(session: AsyncSession = Depends(get_db_session)) -> dict:
    rows = (await session.execute(select(Organization).where(Organization.deleted_at.is_(None)).order_by(Organization.name))).scalars()
    return {"data": [{"slug": item.slug, "name": item.name} for item in rows]}


@router.post("/ingestion/text", status_code=201)
async def ingest_text_evidence(
    request: IngestTextRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """Ingest pasted evidence with author, service and knowledge-area provenance."""
    return await _persist(request, session)


@router.post("/ingestion/bulk", status_code=201)
async def ingest_bulk_evidence(
    request: BulkIngestRequest, session: AsyncSession = Depends(get_db_session)
) -> dict:
    """Ingest up to 100 bounded records in a single transaction."""
    results = [await _persist(item, session) for item in request.records]
    return {"results": results, "ingested": sum(not item["duplicate"] for item in results), "duplicates": sum(item["duplicate"] for item in results)}


@router.post("/ingestion/upload", status_code=201)
async def upload_evidence(
    file: UploadFile = File(...),
    organization_slug: str = Form("default"),
    organization_name: str = Form("My workspace"),
    title: str | None = Form(None),
    source_type: SourceType = Form("document"),
    author_name: str | None = Form(None),
    service_name: str | None = Form(None),
    knowledge_areas: str = Form("[]"),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Upload a PDF, DOCX, text, code or configuration file with provenance."""
    payload = await file.read()
    if len(payload) > 5_000_000:
        raise HTTPException(status_code=413, detail="Files must be 5 MB or smaller in this deployment.")
    try:
        areas = json.loads(knowledge_areas)
        if not isinstance(areas, list) or not all(isinstance(value, str) for value in areas):
            raise ValueError("knowledge_areas must be a JSON array of strings")
        content = _upload_text(file, payload)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return await _persist(IngestTextRequest(
        organization_slug=organization_slug,
        organization_name=organization_name,
        title=title or file.filename or "Uploaded evidence",
        content=content,
        source_type=source_type,
        file_name=file.filename or "upload.txt",
        author_name=author_name,
        service_name=service_name,
        knowledge_areas=areas,
    ), session)


@router.post("/analysis/recompute")
async def recompute_analysis(
    organization_slug: str = "default", session: AsyncSession = Depends(get_db_session)
) -> dict:
    result = await session.execute(select(Organization).where(Organization.slug == organization_slug))
    organization = result.scalar_one_or_none()
    if organization is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    await recompute_workspace(session, organization)
    return {"status": "completed", "organization_slug": organization.slug}
