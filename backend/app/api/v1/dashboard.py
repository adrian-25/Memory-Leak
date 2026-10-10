"""Demo-ready MVP endpoints for the MemoryLeak decision console.

The records are deliberately synthetic and deterministic.  They give the UI an
end-to-end workflow before a customer imports organizational data, and never
represent real employee-performance data.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["intelligence"])


def _now() -> str:
    return datetime.now(UTC).isoformat()


PEOPLE = [
    {"id": "maya-patel", "name": "Maya Patel", "role": "Staff engineer", "team": "Payments", "areas": ["Payment reconciliation", "Ledger recovery"]},
    {"id": "liam-brooks", "name": "Liam Brooks", "role": "Senior engineer", "team": "Platform", "areas": ["Deployment platform", "Service ownership"]},
    {"id": "zoe-martin", "name": "Zoe Martin", "role": "Engineering manager", "team": "Data", "areas": ["Data retention", "Reporting"]},
]

RISKS = [
    {"id": "risk-reconciliation", "title": "Payment reconciliation has a single active expert", "severity": "critical", "score": 0.92, "category": "Bus factor", "owner": "Maya Patel", "service": "Ledger service", "evidence": "42 commits and 9 incident resolutions were authored by one person in the last 90 days.", "confidence": 0.88},
    {"id": "risk-runbook", "title": "Ledger recovery runbook is stale", "severity": "high", "score": 0.78, "category": "Documentation", "owner": "Payments team", "service": "Ledger service", "evidence": "The recovery document has not been updated since the last schema change, 147 days ago.", "confidence": 0.82},
    {"id": "risk-deploy", "title": "Deployment approvals are concentrated", "severity": "high", "score": 0.71, "category": "Knowledge concentration", "owner": "Liam Brooks", "service": "Release platform", "evidence": "One contributor approved 81% of production-release changes this quarter.", "confidence": 0.79},
    {"id": "risk-data", "title": "Retention policy has incomplete service coverage", "severity": "medium", "score": 0.54, "category": "Coverage", "owner": "Data team", "service": "Analytics pipeline", "evidence": "Three of eight dependent services do not cite a current retention policy.", "confidence": 0.74},
]

RECOMMENDATIONS = [
    {"id": "rec-pairing", "priority": "critical", "title": "Schedule a reconciliation knowledge-transfer session", "description": "Pair Maya Patel with a backup owner to walk through the recovery path and record the session in the runbook.", "risk_id": "risk-reconciliation", "evidence_count": 6, "status": "open"},
    {"id": "rec-runbook", "priority": "high", "title": "Refresh the ledger recovery runbook", "description": "Document the schema-change rollback and validate it during the next incident drill.", "risk_id": "risk-runbook", "evidence_count": 4, "status": "open"},
    {"id": "rec-release", "priority": "high", "title": "Add a second release approver", "description": "Rotate deployment review responsibility across two trained platform engineers.", "risk_id": "risk-deploy", "evidence_count": 5, "status": "in_progress"},
]

KNOWLEDGE = [
    {"id": "payment-reconciliation", "name": "Payment reconciliation", "category": "Domain", "experts": 1, "concentration": 0.92, "coverage": 0.41, "severity": "critical"},
    {"id": "ledger-recovery", "name": "Ledger recovery", "category": "Operations", "experts": 2, "concentration": 0.78, "coverage": 0.53, "severity": "high"},
    {"id": "release-platform", "name": "Release platform", "category": "Technology", "experts": 2, "concentration": 0.71, "coverage": 0.68, "severity": "high"},
    {"id": "data-retention", "name": "Data retention", "category": "Policy", "experts": 3, "concentration": 0.42, "coverage": 0.72, "severity": "medium"},
]


@router.get("/dashboard")
async def dashboard() -> dict[str, Any]:
    """Return the complete synthetic workspace used by the MVP dashboard."""
    return {
        "mode": "synthetic_demo",
        "generated_at": _now(),
        "notice": "Synthetic data for product evaluation. Risk scores are organizational signals, not employee-performance measures.",
        "overview": {
            "organizational_risk": 68,
            "risk_trend": -6,
            "knowledge_areas": len(KNOWLEDGE),
            "documents_covered": 64,
            "coverage_trend": 8,
            "at_risk_services": 3,
            "recommendations_open": 2,
            "severity_counts": {"critical": 1, "high": 2, "medium": 1, "low": 0},
        },
        "risks": RISKS,
        "recommendations": RECOMMENDATIONS,
        "knowledge_areas": KNOWLEDGE,
        "people": PEOPLE,
        "graph": {
            "nodes": [
                {"id": "maya-patel", "label": "Maya Patel", "kind": "person"},
                {"id": "payment-reconciliation", "label": "Payment reconciliation", "kind": "knowledge"},
                {"id": "ledger-service", "label": "Ledger service", "kind": "service"},
                {"id": "liam-brooks", "label": "Liam Brooks", "kind": "person"},
                {"id": "release-platform", "label": "Release platform", "kind": "service"},
            ],
            "edges": [
                {"from": "maya-patel", "to": "payment-reconciliation", "label": "primary expert"},
                {"from": "payment-reconciliation", "to": "ledger-service", "label": "supports"},
                {"from": "liam-brooks", "to": "release-platform", "label": "approves"},
            ],
        },
    }


@router.get("/risks")
async def list_risks() -> dict[str, Any]:
    return {"data": RISKS, "generated_at": _now()}


@router.get("/knowledge")
async def list_knowledge() -> dict[str, Any]:
    return {"data": KNOWLEDGE, "generated_at": _now()}


@router.get("/recommendations")
async def list_recommendations() -> dict[str, Any]:
    return {"data": RECOMMENDATIONS, "generated_at": _now()}


class SimulationRequest(BaseModel):
    person_id: str = Field(min_length=1)


@router.post("/simulation")
async def simulate_departure(request: SimulationRequest) -> dict[str, Any]:
    person = next((item for item in PEOPLE if item["id"] == request.person_id), PEOPLE[0])
    is_maya = person["id"] == "maya-patel"
    return {
        "label": "SIMULATION / ESTIMATE — not a prediction of employee behavior or intent.",
        "person": person,
        "risk_delta": 24 if is_maya else 11,
        "affected_services": ["Ledger service", "Payments API"] if is_maya else ["Release platform", "Deployment API"],
        "affected_areas": person["areas"],
        "backup_experts": ["No validated backup expert" if is_maya else "Zoe Martin — partial evidence"],
        "recommended_actions": [
            "Record a paired walkthrough of the high-risk workflow.",
            "Assign and validate a backup owner during the next operating cycle.",
            "Refresh the related runbook before the next release.",
        ],
        "confidence": 0.78 if is_maya else 0.69,
    }


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@router.post("/query")
async def grounded_query(request: QueryRequest) -> dict[str, Any]:
    query = request.question.lower()
    selected = RISKS[0] if any(word in query for word in ("payment", "ledger", "maya", "reconciliation")) else RISKS[2]
    return {
        "answer": f"The strongest currently available signal is: {selected['title']}. {selected['evidence']}",
        "grounded": True,
        "citations": [
            {"source": "Synthetic commit history", "detail": selected["evidence"]},
            {"source": "Risk score", "detail": f"{selected['category']} score {selected['score']:.0%}, confidence {selected['confidence']:.0%}."},
        ],
        "limitations": "This answer uses synthetic demonstration data and must not be used for employment decisions.",
    }
