"""Persistent workspace ingestion and explainable risk analysis.

The service deliberately uses transparent, deterministic calculations.  It is
not an employee-performance system: it measures coverage of documented work
and contribution evidence supplied to a workspace.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Document,
    DocumentChunk,
    EvidenceRecord,
    ExpertiseScore,
    KnowledgeArea,
    Organization,
    Person,
    RawSource,
    Recommendation,
    RiskScore,
    Service,
)

NOTICE = (
    "Workspace signals describe knowledge resilience and documentation coverage. "
    "They are not employee-performance measures and must not be used for employment decisions."
)


def slugify(value: str) -> str:
    """Return a stable, safe identifier without exposing an email address."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:100] or "unknown"


def chunk_text(content: str, size: int = 1200) -> list[tuple[int, int, str]]:
    """Split evidence into small provenance-preserving chunks."""
    clean = content.strip()
    if not clean:
        return []
    chunks: list[tuple[int, int, str]] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        if end < len(clean):
            boundary = clean.rfind("\n", start, end)
            if boundary > start + 300:
                end = boundary
        chunks.append((start, end, clean[start:end]))
        start = end
    return chunks


async def get_or_create_organization(
    session: AsyncSession, slug: str, name: str
) -> Organization:
    normalized_slug = slugify(slug)
    result = await session.execute(select(Organization).where(Organization.slug == normalized_slug))
    organization = result.scalar_one_or_none()
    if organization is None:
        organization = Organization(slug=normalized_slug, name=name.strip() or "Untitled workspace")
        session.add(organization)
        await session.flush()
    return organization


async def _get_or_create_person(
    session: AsyncSession, organization: Organization, display_name: str
) -> Person:
    synthetic_id = f"{organization.slug}:{slugify(display_name)}"
    result = await session.execute(select(Person).where(Person.synthetic_id == synthetic_id))
    person = result.scalar_one_or_none()
    if person is None:
        person = Person(
            organization_id=organization.id,
            display_name=display_name.strip(),
            synthetic_id=synthetic_id,
            role_title="Workspace contributor",
        )
        session.add(person)
        await session.flush()
    return person


async def _get_or_create_service(
    session: AsyncSession, organization: Organization, name: str
) -> Service:
    result = await session.execute(
        select(Service).where(Service.organization_id == organization.id, Service.name == name)
    )
    service = result.scalar_one_or_none()
    if service is None:
        service = Service(
            organization_id=organization.id,
            name=name.strip(),
            criticality="high",
        )
        session.add(service)
        await session.flush()
    return service


async def _get_or_create_area(
    session: AsyncSession, organization: Organization, name: str
) -> KnowledgeArea:
    result = await session.execute(
        select(KnowledgeArea).where(
            KnowledgeArea.organization_id == organization.id, KnowledgeArea.name == name
        )
    )
    area = result.scalar_one_or_none()
    if area is None:
        area = KnowledgeArea(
            organization_id=organization.id,
            name=name.strip(),
            description="Imported workspace knowledge area",
        )
        session.add(area)
        await session.flush()
    return area


async def ingest_text(
    session: AsyncSession,
    *,
    organization_slug: str,
    organization_name: str,
    title: str,
    content: str,
    source_type: str,
    file_name: str,
    author_name: str | None = None,
    service_name: str | None = None,
    knowledge_areas: list[str] | None = None,
    last_modified: datetime | None = None,
) -> dict[str, Any]:
    """Persist a source and its chunks, rejecting duplicate content per organization."""
    if not content.strip():
        raise ValueError("Evidence content cannot be empty.")

    organization = await get_or_create_organization(session, organization_slug, organization_name)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    existing = await session.execute(
        select(RawSource).where(
            RawSource.organization_id == organization.id, RawSource.content_hash == content_hash
        )
    )
    if existing.scalar_one_or_none() is not None:
        return {"duplicate": True, "organization_slug": organization.slug, "content_hash": content_hash}

    person = (
        await _get_or_create_person(session, organization, author_name)
        if author_name and author_name.strip()
        else None
    )
    service = (
        await _get_or_create_service(session, organization, service_name)
        if service_name and service_name.strip()
        else None
    )
    areas = [
        await _get_or_create_area(session, organization, area)
        for area in dict.fromkeys(area.strip() for area in (knowledge_areas or []) if area.strip())
    ]
    raw = RawSource(
        organization_id=organization.id,
        source_type=source_type,
        file_name=file_name or f"{slugify(title)}.txt",
        file_path=f"api://workspace/{organization.slug}/{content_hash[:12]}",
        content_hash=content_hash,
        file_size_bytes=len(content.encode("utf-8")),
        status="processing",
    )
    session.add(raw)
    await session.flush()
    document = Document(
        organization_id=organization.id,
        raw_source_id=raw.id,
        title=title.strip() or file_name,
        document_type=source_type,
        author_name=person.display_name if person else None,
        author_id=person.id if person else None,
        last_modified=last_modified or datetime.now(UTC),
        word_count=len(content.split()),
        content_hash=content_hash,
        metadata_={
            "service_id": str(service.id) if service else None,
            "service_name": service.name if service else None,
            "knowledge_area_ids": [str(area.id) for area in areas],
            "knowledge_areas": [area.name for area in areas],
            "ingestion": "api",
        },
    )
    session.add(document)
    await session.flush()
    for index, (start, end, text) in enumerate(chunk_text(content)):
        session.add(
            DocumentChunk(
                document_id=document.id,
                organization_id=organization.id,
                chunk_index=index,
                content=text,
                token_count=len(text.split()),
                start_char=start,
                end_char=end,
            )
        )
    raw.status = "completed"
    await session.flush()
    await recompute_workspace(session, organization)
    return {
        "duplicate": False,
        "organization_slug": organization.slug,
        "document_id": str(document.id),
        "content_hash": content_hash,
        "chunks_created": len(chunk_text(content)),
    }


def severity(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


async def recompute_workspace(session: AsyncSession, organization: Organization) -> None:
    """Recompute transparent coverage/concentration scores from stored evidence."""
    documents = list(
        (await session.execute(select(Document).where(Document.organization_id == organization.id))).scalars()
    )
    await session.execute(delete(EvidenceRecord).where(EvidenceRecord.organization_id == organization.id))
    await session.execute(delete(Recommendation).where(Recommendation.organization_id == organization.id))
    await session.execute(delete(RiskScore).where(RiskScore.organization_id == organization.id))
    await session.execute(delete(ExpertiseScore).where(ExpertiseScore.organization_id == organization.id))
    if not documents:
        return

    people = {person.id: person for person in (await session.execute(select(Person).where(Person.organization_id == organization.id))).scalars()}
    areas = {str(area.id): area for area in (await session.execute(select(KnowledgeArea).where(KnowledgeArea.organization_id == organization.id))).scalars()}
    services = {str(service.id): service for service in (await session.execute(select(Service).where(Service.organization_id == organization.id))).scalars()}
    by_area: dict[str, Counter[Any]] = defaultdict(Counter)
    by_service: dict[str, list[Document]] = defaultdict(list)
    for document in documents:
        metadata = document.metadata_ or {}
        for area_id in metadata.get("knowledge_area_ids", []):
            if document.author_id:
                by_area[str(area_id)][document.author_id] += 1
        if metadata.get("service_id"):
            by_service[str(metadata["service_id"])].append(document)

    for area_id, contributions in by_area.items():
        total = sum(contributions.values())
        for person_id, count in contributions.items():
            if area_id not in areas or person_id not in people:
                continue
            share = count / total
            session.add(
                ExpertiseScore(
                    organization_id=organization.id,
                    person_id=person_id,
                    knowledge_area_id=areas[area_id].id,
                    score=share,
                    recency_score=1.0,
                    breadth_score=min(1.0, count / 3),
                    depth_score=min(1.0, count / 4),
                    confidence=min(0.95, 0.55 + count * 0.1),
                    evidence_count=count,
                )
            )

    risk_rows: list[tuple[RiskScore, Service | None, list[Document]]] = []
    for service_id, service_documents in by_service.items():
        service = services.get(service_id)
        if not service:
            continue
        authors = Counter(document.author_id for document in service_documents if document.author_id)
        total = len(service_documents)
        concentration = max(authors.values(), default=0) / total
        coverage_penalty = max(0.0, 1 - min(total, 4) / 4)
        score = min(1.0, 0.2 + 0.65 * concentration + 0.15 * coverage_penalty)
        owner_id, owner_count = authors.most_common(1)[0] if authors else (None, 0)
        owner = people.get(owner_id)
        risk = RiskScore(
            organization_id=organization.id,
            entity_type="service",
            entity_id=service.id,
            risk_category="bus_factor",
            score=score,
            severity=severity(score),
            confidence=min(0.95, 0.5 + total * 0.08),
            contributing_factors=[
                {"metric": "evidence_documents", "value": total},
                {"metric": "active_contributors", "value": len(authors)},
                {"metric": "largest_evidence_share", "value": round(concentration, 2)},
                {"metric": "primary_contributor", "value": owner.display_name if owner else "Unattributed"},
                {"metric": "primary_contributor_documents", "value": owner_count},
            ],
            limitations="Contribution evidence is a proxy for knowledge coverage; it does not measure individual ability or performance.",
        )
        session.add(risk)
        await session.flush()
        evidence_document = service_documents[0]
        session.add(EvidenceRecord(
            organization_id=organization.id,
            claim_type="risk",
            claim_id=risk.id,
            source_type="document",
            source_id=evidence_document.id,
            excerpt=f"{total} imported evidence document(s) mapped to {service.name}.",
            inference_type="aggregated",
            confidence=risk.confidence,
        ))
        risk_rows.append((risk, service, service_documents))
        session.add(Recommendation(
            organization_id=organization.id,
            recommendation_type="knowledge_transfer",
            priority=severity(score) if severity(score) != "low" else "medium",
            title=f"Validate backup coverage for {service.name}",
            description=(
                f"Document a paired walkthrough for {service.name} and validate a second contributor. "
                f"Current evidence includes {len(authors)} contributor(s) across {total} document(s)."
            ),
            target_entity_type="service",
            target_entity_id=service.id,
            risk_score_id=risk.id,
            evidence_ids=[],
            status="open",
        ))

    overall = sum(float(row.score) for row, _, _ in risk_rows) / len(risk_rows) if risk_rows else 0.0
    overall_risk = RiskScore(
        organization_id=organization.id,
        entity_type="organization",
        entity_id=organization.id,
        risk_category="overall",
        score=overall,
        severity=severity(overall),
        confidence=0.7 if risk_rows else 0.0,
        contributing_factors=[{"metric": "assessed_services", "value": len(risk_rows)}],
        limitations="Aggregate of evidence-backed service coverage signals.",
    )
    session.add(overall_risk)


def _factor(factors: list[dict[str, Any]], metric: str, fallback: Any = None) -> Any:
    return next((item.get("value") for item in factors if item.get("metric") == metric), fallback)


async def workspace_dashboard(session: AsyncSession, organization_slug: str = "default") -> dict[str, Any] | None:
    result = await session.execute(select(Organization).where(Organization.slug == organization_slug))
    organization = result.scalar_one_or_none()
    if organization is None:
        return None
    documents = list((await session.execute(select(Document).where(Document.organization_id == organization.id))).scalars())
    if not documents:
        return None
    people = {person.id: person for person in (await session.execute(select(Person).where(Person.organization_id == organization.id))).scalars()}
    services = {service.id: service for service in (await session.execute(select(Service).where(Service.organization_id == organization.id))).scalars()}
    areas = list((await session.execute(select(KnowledgeArea).where(KnowledgeArea.organization_id == organization.id))).scalars())
    expertise = list((await session.execute(select(ExpertiseScore).where(ExpertiseScore.organization_id == organization.id))).scalars())
    risks = list((await session.execute(select(RiskScore).where(RiskScore.organization_id == organization.id, RiskScore.entity_type == "service").order_by(RiskScore.score.desc()))).scalars())
    recommendations = list((await session.execute(select(Recommendation).where(Recommendation.organization_id == organization.id).order_by(Recommendation.created_at.desc()))).scalars())
    evidence = list((await session.execute(select(EvidenceRecord).where(EvidenceRecord.organization_id == organization.id))).scalars())
    risk_data = []
    for risk in risks:
        service = services.get(risk.entity_id)
        owner = _factor(risk.contributing_factors, "primary_contributor", "Unattributed")
        total = _factor(risk.contributing_factors, "evidence_documents", 0)
        contributor_count = _factor(risk.contributing_factors, "active_contributors", 0)
        risk_data.append({
            "id": str(risk.id), "title": f"{service.name if service else 'Service'} has concentrated knowledge evidence",
            "severity": risk.severity, "score": float(risk.score), "category": "Knowledge concentration",
            "owner": owner, "service": service.name if service else "Unknown service",
            "evidence": f"{total} imported evidence document(s) are mapped to this service across {contributor_count} contributor(s).",
            "confidence": float(risk.confidence),
        })
    area_documents: dict[str, list[Document]] = defaultdict(list)
    for document in documents:
        for area_id in (document.metadata_ or {}).get("knowledge_area_ids", []):
            area_documents[str(area_id)].append(document)
    knowledge = []
    for area in areas:
        scores = [float(item.score) for item in expertise if item.knowledge_area_id == area.id]
        docs = area_documents.get(str(area.id), [])
        concentration = max(scores, default=0.0)
        coverage = min(1.0, len(docs) / 4)
        knowledge.append({"id": str(area.id), "name": area.name, "category": "Imported", "experts": len(scores), "concentration": concentration, "coverage": coverage, "severity": severity(concentration)})
    counts = Counter(risk["severity"] for risk in risk_data)
    org_risk = round((sum(risk["score"] for risk in risk_data) / len(risk_data) if risk_data else 0) * 100)
    coverage = round(min(100, len(documents) / max(1, len(services)) / 4 * 100))
    person_data = [{"id": str(person.id), "name": person.display_name, "role": person.role_title or "Contributor", "team": "Workspace", "areas": [area.name for area in areas if any(score.person_id == person.id and score.knowledge_area_id == area.id for score in expertise)]} for person in people.values()]
    graph_nodes = ([{"id": str(person.id), "label": person.display_name, "kind": "person"} for person in people.values()] + [{"id": str(area.id), "label": area.name, "kind": "knowledge"} for area in areas] + [{"id": str(service.id), "label": service.name, "kind": "service"} for service in services.values()])
    graph_edges = []
    for score in expertise:
        graph_edges.append({"from": str(score.person_id), "to": str(score.knowledge_area_id), "label": "has evidence in"})
    for document in documents:
        for area_id in (document.metadata_ or {}).get("knowledge_area_ids", []):
            service_id = (document.metadata_ or {}).get("service_id")
            if service_id:
                graph_edges.append({"from": str(area_id), "to": str(service_id), "label": "supports"})
    return {
        "mode": "workspace", "generated_at": datetime.now(UTC).isoformat(), "organization": {"slug": organization.slug, "name": organization.name}, "notice": NOTICE,
        "overview": {"organizational_risk": org_risk, "risk_trend": 0, "knowledge_areas": len(knowledge), "documents_covered": coverage, "coverage_trend": 0, "at_risk_services": len(risk_data), "recommendations_open": sum(rec.status == "open" for rec in recommendations), "severity_counts": {level: counts.get(level, 0) for level in ("critical", "high", "medium", "low")}, "evidence_documents": len(documents), "evidence_records": len(evidence)},
        "risks": risk_data,
        "recommendations": [{"id": str(rec.id), "priority": rec.priority, "title": rec.title, "description": rec.description, "risk_id": str(rec.risk_score_id) if rec.risk_score_id else None, "evidence_count": 1, "status": rec.status} for rec in recommendations],
        "knowledge_areas": knowledge, "people": person_data, "graph": {"nodes": graph_nodes, "edges": graph_edges},
    }


async def workspace_simulation(session: AsyncSession, person_id: str) -> dict[str, Any] | None:
    """Estimate resilience loss from the evidence graph, never a departure prediction."""
    try:
        person_uuid = uuid.UUID(person_id)
    except ValueError:
        return None
    person = (await session.execute(select(Person).where(Person.id == person_uuid))).scalar_one_or_none()
    if person is None:
        return None
    documents = list((await session.execute(select(Document).where(Document.organization_id == person.organization_id, Document.author_id == person.id))).scalars())
    if not documents:
        return None
    services = {item.id: item for item in (await session.execute(select(Service).where(Service.organization_id == person.organization_id))).scalars()}
    people = {item.id: item for item in (await session.execute(select(Person).where(Person.organization_id == person.organization_id))).scalars()}
    areas = {item.id: item for item in (await session.execute(select(KnowledgeArea).where(KnowledgeArea.organization_id == person.organization_id))).scalars()}
    affected_service_ids = {str((document.metadata_ or {}).get("service_id")) for document in documents if (document.metadata_ or {}).get("service_id")}
    area_ids = {str(area_id) for document in documents for area_id in (document.metadata_ or {}).get("knowledge_area_ids", [])}
    backups: set[str] = set()
    for service_id in affected_service_ids:
        related = list((await session.execute(select(Document).where(Document.organization_id == person.organization_id))).scalars())
        for document in related:
            if str((document.metadata_ or {}).get("service_id")) == service_id and document.author_id and document.author_id != person.id:
                backup = people.get(document.author_id)
                if backup:
                    backups.add(backup.display_name)
    affected_services = [services[uuid.UUID(value)].name for value in affected_service_ids if uuid.UUID(value) in services]
    affected_areas = [areas[uuid.UUID(value)].name for value in area_ids if uuid.UUID(value) in areas]
    return {
        "label": "SIMULATION / ESTIMATE — not a prediction of employee behavior or intent.",
        "person": {"id": str(person.id), "name": person.display_name, "role": person.role_title or "Contributor"},
        "risk_delta": min(60, 8 + len(documents) * 8 + len(affected_services) * 6),
        "affected_services": affected_services or ["No service mapping in the imported evidence"],
        "affected_areas": affected_areas or ["No knowledge-area mapping in the imported evidence"],
        "backup_experts": sorted(backups) or ["No validated backup evidence"],
        "recommended_actions": [
            "Record a paired walkthrough of the documented workflow.",
            "Assign and validate a backup owner using fresh evidence.",
            "Add evidence from a second contributor before using the result operationally.",
        ],
        "confidence": min(0.9, 0.45 + len(documents) * 0.08),
    }


async def workspace_query(session: AsyncSession, question: str, organization_slug: str = "default") -> dict[str, Any] | None:
    """Return a citation-first lexical retrieval answer from imported evidence."""
    organization = (await session.execute(select(Organization).where(Organization.slug == organization_slug))).scalar_one_or_none()
    if organization is None:
        return None
    documents = list((await session.execute(select(Document).where(Document.organization_id == organization.id))).scalars())
    if not documents:
        return None
    terms = {term for term in re.findall(r"[a-z0-9]{3,}", question.lower()) if term not in {"what", "should", "would", "with", "from", "about", "this", "that", "have", "does"}}
    scored: list[tuple[int, Document, str]] = []
    for document in documents:
        chunks = list((await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id).order_by(DocumentChunk.chunk_index))).scalars())
        text = " ".join(chunk.content for chunk in chunks)
        score = sum(term in text.lower() or term in (document.title or "").lower() for term in terms)
        if score:
            scored.append((score, document, text))
    if not scored:
        return {"answer": "I don’t have enough imported evidence to support an answer to that question.", "grounded": False, "citations": [], "limitations": "Import relevant documents, code, issues, or discussions first. The assistant does not invent unsupported claims."}
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = scored[:3]
    citations = [{"source": document.title or document.document_type, "detail": text[:280].replace("\n", " ").strip()} for _, document, text in selected]
    return {"answer": f"I found {len(selected)} relevant imported evidence source(s). The strongest match is \"{citations[0]['source']}\": {citations[0]['detail']}", "grounded": True, "citations": citations, "limitations": "This answer is limited to imported workspace evidence and is not a conclusion about employee performance or intent."}
