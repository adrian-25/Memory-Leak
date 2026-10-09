# MemoryLeak — API Specification

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Base URL:** `/api/v1`
**Authentication:** Bearer JWT token (all endpoints except `/health` and `/auth/token`)
**Content-Type:** `application/json` (except file upload endpoints)
**Last Updated:** 2026-09-03

---

## 1. Conventions

### Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Resource created |
| 400 | Validation error |
| 401 | Unauthorized (no or invalid token) |
| 403 | Forbidden (insufficient role) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate content hash) |
| 422 | Unprocessable entity (Pydantic validation error) |
| 500 | Internal server error |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'source_type' must be one of: pdf, docx, markdown...",
    "details": [
      {
        "field": "source_type",
        "message": "invalid value"
      }
    ]
  }
}
```

### Pagination

All list endpoints support:
- `page` (integer, default: 1)
- `page_size` (integer, default: 20, max: 100)

Response envelope for paginated results:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 342,
    "total_pages": 18
  }
}
```

---

## 2. Health and System Endpoints

### `GET /health`

Returns system health status. No authentication required.

**Response 200:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "services": {
    "postgres": "ok",
    "neo4j": "ok",
    "pgvector": "ok"
  },
  "timestamp": "2026-09-03T20:00:00Z"
}
```

---

### `GET /api/v1/analytics`

Returns aggregate system statistics.

**Required role:** Viewer

**Response 200:**
```json
{
  "documents_total": 842,
  "chunks_total": 14230,
  "people_total": 52,
  "services_total": 24,
  "knowledge_areas_total": 108,
  "risk_scores_computed_at": "2026-09-03T19:00:00Z",
  "risks_by_severity": {
    "critical": 3,
    "high": 12,
    "medium": 31,
    "low": 47,
    "info": 22
  },
  "documentation_coverage_average": 0.64,
  "bus_factor_1_services": 7,
  "stale_documents_count": 23
}
```

---

## 3. Authentication Endpoints

### `POST /api/v1/auth/token`

Obtain a JWT access token.

**Request Body:**
```json
{
  "email": "analyst@example.com",
  "password": "securepassword"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

---

### `POST /api/v1/auth/refresh`

Exchange a refresh token for a new access token.

**Request Body:**
```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

**Response 200:** Same as `/auth/token`

---

### `POST /api/v1/auth/logout`

Invalidate the current session. (MVP: client-side token discard; no server-side revocation.)

**Response 200:**
```json
{ "message": "Logged out successfully" }
```

---

## 4. Ingestion Endpoints

### `POST /api/v1/ingestion/upload`

Upload a document or data file for ingestion.

**Required role:** Analyst, Admin
**Content-Type:** `multipart/form-data`

**Form Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | binary | Yes | The file to upload |
| `source_type` | string | Yes | One of: `pdf`, `docx`, `markdown`, `txt`, `python`, `javascript`, `typescript`, `java`, `sql`, `yaml`, `json`, `toml`, `ini`, `issues`, `commits`, `discussions` |
| `metadata` | JSON string | No | Additional metadata: `{"project_id": "...", "service_id": "..."}` |

**Response 201:**
```json
{
  "id": "a7f2c1b0-...",
  "file_name": "payment-service-docs.pdf",
  "source_type": "pdf",
  "content_hash": "sha256:abc123...",
  "status": "pending",
  "created_at": "2026-09-03T20:01:00Z"
}
```

**Response 409 (Duplicate):**
```json
{
  "error": {
    "code": "DUPLICATE_CONTENT",
    "message": "A document with this content hash has already been ingested.",
    "existing_id": "9e1d3f22-..."
  }
}
```

---

### `POST /api/v1/ingestion/bulk`

Submit multiple files or a dataset directory for bulk ingestion.

**Required role:** Admin
**Content-Type:** `multipart/form-data`

**Form Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | binary[] | Yes | Array of files |
| `source_type_map` | JSON string | Yes | Maps filename to source_type |

**Response 202:**
```json
{
  "job_id": "b9f3a1...",
  "submitted_count": 48,
  "status": "queued",
  "created_at": "2026-09-03T20:01:30Z"
}
```

---

### `GET /api/v1/ingestion/jobs`

List ingestion jobs.

**Required role:** Analyst, Admin

**Query Parameters:**
- `status`: filter by `pending | processing | completed | failed`
- `page`, `page_size`

**Response 200:**
```json
{
  "data": [
    {
      "id": "a7f2c1b0-...",
      "file_name": "payment-service-docs.pdf",
      "source_type": "pdf",
      "status": "completed",
      "created_at": "2026-09-03T20:01:00Z",
      "completed_at": "2026-09-03T20:01:45Z"
    }
  ],
  "pagination": { ... }
}
```

---

### `GET /api/v1/ingestion/jobs/{job_id}`

Get status and result detail for a specific ingestion job.

**Required role:** Analyst, Admin

**Response 200:**
```json
{
  "id": "a7f2c1b0-...",
  "file_name": "payment-service-docs.pdf",
  "source_type": "pdf",
  "status": "completed",
  "document_id": "d4e5f6...",
  "chunks_created": 47,
  "entities_extracted": 23,
  "embeddings_generated": 47,
  "error_message": null,
  "created_at": "2026-09-03T20:01:00Z",
  "completed_at": "2026-09-03T20:01:45Z"
}
```

---

## 5. Knowledge Endpoints

### `GET /api/v1/knowledge`

List knowledge areas.

**Required role:** Viewer

**Query Parameters:**
- `category`: filter by category
- `search`: text search on name/description
- `page`, `page_size`

**Response 200:**
```json
{
  "data": [
    {
      "id": "ka-001-...",
      "name": "Payment Reconciliation",
      "category": "domain",
      "description": "...",
      "expert_count": 2,
      "concentration_score": 0.87,
      "severity": "high"
    }
  ],
  "pagination": { ... }
}
```

---

### `GET /api/v1/knowledge/{id}`

Get a single knowledge area with full detail.

**Required role:** Viewer

**Response 200:**
```json
{
  "id": "ka-001-...",
  "name": "Payment Reconciliation",
  "category": "domain",
  "description": "...",
  "parent_area": null,
  "child_areas": [],
  "experts": [
    {
      "person_id": "p-001-...",
      "display_name": "Alice Chen",
      "score": 0.91,
      "confidence": 0.84,
      "evidence_count": 47
    }
  ],
  "related_services": ["payment-service", "ledger-service"],
  "related_documents": 12,
  "risk": {
    "concentration_score": 0.87,
    "staleness_score": 0.23,
    "severity": "high"
  }
}
```

---

## 6. Risk Endpoints

### `GET /api/v1/risks`

List risk scores with filters.

**Required role:** Viewer

**Query Parameters:**
- `severity`: `critical | high | medium | low | info`
- `category`: `bus_factor | knowledge_concentration | documentation_coverage | documentation_staleness | doc_code_drift | dependency_risk | overall`
- `entity_type`: `person | service | project | knowledge_area | organization`
- `team_id`: UUID
- `project_id`: UUID
- `page`, `page_size`

**Response 200:**
```json
{
  "data": [
    {
      "id": "r-001-...",
      "entity_type": "service",
      "entity_id": "svc-payment-...",
      "entity_name": "payment-service",
      "risk_category": "bus_factor",
      "score": 0.92,
      "severity": "critical",
      "confidence": 0.79,
      "computed_at": "2026-09-03T19:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### `GET /api/v1/risks/{id}`

Get a full risk record with evidence and explanation.

**Required role:** Viewer

**Response 200:**
```json
{
  "id": "r-001-...",
  "entity_type": "service",
  "entity_id": "svc-payment-...",
  "entity_name": "payment-service",
  "risk_category": "bus_factor",
  "score": 0.92,
  "severity": "critical",
  "confidence": 0.79,
  "contributing_factors": [
    {
      "factor": "Single expert identified",
      "weight": 0.55,
      "detail": "Alice Chen accounts for 87% of commits and 91% of issue resolutions."
    },
    {
      "factor": "No secondary expert",
      "weight": 0.30,
      "detail": "No other person has a KNOWS relationship to Payment Reconciliation with score > 0.3."
    },
    {
      "factor": "Critical service",
      "weight": 0.15,
      "detail": "payment-service has criticality=critical."
    }
  ],
  "limitations": "Score based on commit and issue data only. Does not incorporate verbal knowledge transfer that left no written record.",
  "evidence": [
    {
      "id": "ev-001-...",
      "source_type": "commit",
      "source_id": "c-abc123-...",
      "excerpt": "Fix reconciliation edge case in netting engine",
      "confidence": 0.91,
      "inference_type": "direct"
    }
  ],
  "recommendations": [
    {
      "id": "rec-001-...",
      "type": "backup_expert",
      "priority": "critical",
      "title": "Identify and develop a backup expert for Payment Reconciliation"
    }
  ],
  "computed_at": "2026-09-03T19:00:00Z"
}
```

---

## 7. People Endpoints

### `GET /api/v1/people`

List people.

**Required role:** Viewer

**Query Parameters:**
- `team_id`: UUID
- `is_active`: boolean
- `search`: text search
- `page`, `page_size`

**Response 200:**
```json
{
  "data": [
    {
      "id": "p-001-...",
      "display_name": "Alice Chen",
      "role_title": "Senior Engineer",
      "team_name": "Payments Team",
      "is_active": true,
      "knowledge_area_count": 8,
      "overall_risk_involvement": "critical"
    }
  ],
  "pagination": { ... }
}
```

---

### `GET /api/v1/people/{id}`

Get a full person profile.

**Required role:** Viewer

**Response 200:**
```json
{
  "id": "p-001-...",
  "display_name": "Alice Chen",
  "role_title": "Senior Engineer",
  "team_name": "Payments Team",
  "is_active": true,
  "knowledge_areas": [
    {
      "area_id": "ka-001-...",
      "area_name": "Payment Reconciliation",
      "score": 0.91,
      "confidence": 0.84,
      "evidence_count": 47
    }
  ],
  "owned_services": ["payment-service"],
  "contribution_summary": {
    "total_commits": 312,
    "issues_resolved": 28,
    "documents_authored": 14,
    "first_activity": "2022-03-15",
    "last_activity": "2026-08-28"
  },
  "risks": [
    {
      "risk_id": "r-001-...",
      "category": "bus_factor",
      "entity_name": "payment-service",
      "severity": "critical",
      "score": 0.92
    }
  ],
  "recommendations": [...]
}
```

---

## 8. Systems / Services Endpoints

### `GET /api/v1/systems`

List services.

**Required role:** Viewer

**Query Parameters:**
- `criticality`: `critical | high | medium | low`
- `project_id`: UUID
- `search`
- `page`, `page_size`

**Response 200:**
```json
{
  "data": [
    {
      "id": "svc-payment-...",
      "name": "payment-service",
      "criticality": "critical",
      "project_name": "Core Banking Platform",
      "primary_owner_name": "Alice Chen",
      "documentation_coverage": 0.42,
      "bus_factor": 1,
      "overall_risk_score": 0.87,
      "severity": "critical"
    }
  ],
  "pagination": { ... }
}
```

---

### `GET /api/v1/systems/{id}`

Get a full system/service profile.

**Required role:** Viewer

**Response 200:**
```json
{
  "id": "svc-payment-...",
  "name": "payment-service",
  "description": "Handles payment initiation, reconciliation, and settlement.",
  "criticality": "critical",
  "project": { ... },
  "primary_owner": { "id": "p-001-...", "display_name": "Alice Chen" },
  "knowledge_owners": [
    {
      "person_id": "p-001-...",
      "display_name": "Alice Chen",
      "coverage_percentage": 87
    }
  ],
  "documentation_coverage": 0.42,
  "undocumented_components": ["netting-engine", "settlement-scheduler"],
  "documentation_staleness": 0.34,
  "bus_factor": 1,
  "risks": [...],
  "recommendations": [...],
  "dependencies": [
    { "service_id": "svc-ledger-...", "name": "ledger-service", "dependency_type": "hard" }
  ],
  "dependents": [
    { "service_id": "svc-billing-...", "name": "billing-service" }
  ]
}
```

---

## 9. Graph Endpoints

### `GET /api/v1/graph`

Get a subgraph for visualization.

**Required role:** Viewer

**Query Parameters:**
- `entity_type`: `person | service | knowledge_area | project`
- `entity_id`: UUID (anchor node)
- `depth`: integer (default: 2, max: 4)
- `relationship_types`: comma-separated list

**Response 200:**
```json
{
  "nodes": [
    {
      "id": "p-001-...",
      "label": "Alice Chen",
      "type": "person",
      "properties": { "is_active": true, "role_title": "Senior Engineer" }
    },
    {
      "id": "ka-001-...",
      "label": "Payment Reconciliation",
      "type": "knowledge_area",
      "properties": { "category": "domain" }
    }
  ],
  "edges": [
    {
      "id": "e-001-...",
      "source": "p-001-...",
      "target": "ka-001-...",
      "type": "KNOWS",
      "properties": { "score": 0.91, "confidence": 0.84 }
    }
  ],
  "meta": {
    "anchor_id": "p-001-...",
    "depth": 2,
    "node_count": 14,
    "edge_count": 21
  }
}
```

---

## 10. Simulation Endpoints

### `POST /api/v1/simulation`

Run a what-if simulation.

**Required role:** Analyst, Admin

**Request Body:**
```json
{
  "scenario_type": "person_departure",
  "entity_id": "p-001-...",
  "parameters": {}
}
```

`scenario_type` options: `person_departure`, `service_decommission`

**Response 200:**
```json
{
  "simulation_id": "sim-001-...",
  "scenario_type": "person_departure",
  "entity": {
    "id": "p-001-...",
    "display_name": "Alice Chen"
  },
  "WARNING": "SIMULATION / ESTIMATE — Results are calculated from available evidence. They do not constitute a prediction of employee behavior, intent, or organizational decisions.",
  "impact": {
    "affected_services": [
      {
        "service_id": "svc-payment-...",
        "name": "payment-service",
        "current_risk_score": 0.87,
        "simulated_risk_score": 0.97,
        "risk_delta": 0.10,
        "orphaned_knowledge_areas": ["Payment Reconciliation", "Netting Engine Logic"]
      }
    ],
    "affected_knowledge_areas": [
      {
        "area_id": "ka-001-...",
        "name": "Payment Reconciliation",
        "remaining_experts": [],
        "status": "no_remaining_expert"
      }
    ],
    "alternative_experts": [
      {
        "area_id": "ka-002-...",
        "area_name": "Payment APIs",
        "alternative": {
          "person_id": "p-003-...",
          "display_name": "Bob Lee",
          "score": 0.41,
          "confidence": 0.60
        }
      }
    ],
    "overall_risk_delta": 0.09
  },
  "evidence_count": 47,
  "confidence": 0.74,
  "computed_at": "2026-09-03T20:05:00Z"
}
```

---

## 11. Recommendations Endpoints

### `GET /api/v1/recommendations`

List recommendations.

**Required role:** Viewer

**Query Parameters:**
- `priority`: `critical | high | medium | low`
- `type`: `document_gap | backup_expert | knowledge_transfer | risk_mitigation`
- `status`: `open | in_progress | resolved | dismissed`
- `entity_id`: UUID
- `page`, `page_size`

**Response 200:**
```json
{
  "data": [
    {
      "id": "rec-001-...",
      "type": "backup_expert",
      "priority": "critical",
      "title": "Develop backup expert for Payment Reconciliation",
      "status": "open",
      "target_entity_type": "knowledge_area",
      "target_entity_name": "Payment Reconciliation",
      "created_at": "2026-09-03T19:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### `GET /api/v1/recommendations/{id}`

Get a recommendation with full evidence.

**Required role:** Viewer

**Response 200:**
```json
{
  "id": "rec-001-...",
  "type": "backup_expert",
  "priority": "critical",
  "title": "Develop backup expert for Payment Reconciliation",
  "description": "Payment Reconciliation is known by only one active person (Alice Chen, score: 0.91). This creates a critical single-point-of-failure. Recommended action: identify a second engineer for cross-training or pair programming sessions.",
  "target_entity_type": "knowledge_area",
  "target_entity_id": "ka-001-...",
  "target_entity_name": "Payment Reconciliation",
  "motivating_risk": {
    "risk_id": "r-001-...",
    "category": "bus_factor",
    "score": 0.92,
    "severity": "critical"
  },
  "evidence": [...],
  "status": "open",
  "created_at": "2026-09-03T19:00:00Z",
  "updated_at": "2026-09-03T19:00:00Z"
}
```

---

### `PATCH /api/v1/recommendations/{id}/status`

Update recommendation status.

**Required role:** Analyst, Admin

**Request Body:**
```json
{
  "status": "in_progress",
  "note": "Scheduled pair programming sessions with Bob Lee for 2026-09-15"
}
```

**Response 200:** Updated recommendation object.

---

## 12. AI Query Endpoint

### `POST /api/v1/query`

Submit a natural-language query to the AI assistant.

**Required role:** Viewer

**Request Body:**
```json
{
  "question": "Who understands the payment reconciliation process and what is the risk if they leave?",
  "filters": {
    "organization_id": "org-001-..."
  }
}
```

**Response 200:**
```json
{
  "query_id": "q-001-...",
  "question": "Who understands the payment reconciliation process and what is the risk if they leave?",
  "answer": "Based on retrieved evidence, Alice Chen (score: 0.91) is the primary expert on Payment Reconciliation. If Alice were to leave, the payment-service would be at critical risk (simulated score: 0.97) as no other active expert has a KNOWS relationship to this knowledge area with score > 0.3.",
  "WARNING": "This answer is generated by an AI system and is based on the evidence retrieved from organizational data. It should not be used as a basis for personnel decisions.",
  "evidence": [
    {
      "source_type": "document",
      "document_title": "Payment Reconciliation Architecture v3",
      "excerpt": "Primary author: Alice Chen. Last updated: 2025-11-02.",
      "similarity_score": 0.89
    },
    {
      "source_type": "graph",
      "entity": "Alice Chen",
      "relationship": "KNOWS",
      "target": "Payment Reconciliation",
      "score": 0.91
    }
  ],
  "retrieval_method": "hybrid",
  "retrieved_chunks": 8,
  "latency_ms": 1240
}
```

---

## 13. User Management Endpoints (Admin)

### `GET /api/v1/users`

List users in the organization.

**Required role:** Admin

**Response 200:** Paginated list of users (without password hashes).

---

### `POST /api/v1/users`

Create a new user.

**Required role:** Admin

**Request Body:**
```json
{
  "email": "newanalyst@example.com",
  "display_name": "Jane Smith",
  "role": "analyst",
  "password": "temporarypassword123"
}
```

**Response 201:** Created user object.

---

### `PATCH /api/v1/users/{id}`

Update user role or active status.

**Required role:** Admin

**Request Body:**
```json
{
  "role": "viewer",
  "is_active": false
}
```

**Response 200:** Updated user object.

---

### `DELETE /api/v1/users/{id}`

Deactivate (soft-delete) a user.

**Required role:** Admin

**Response 200:**
```json
{ "message": "User deactivated." }
```

---

## 14. Evidence Endpoint

### `GET /api/v1/evidence/{claim_type}/{claim_id}`

Retrieve all evidence records for a specific claim (risk score, expertise score).

**Required role:** Viewer

**Path parameters:**
- `claim_type`: `expertise | risk | relationship`
- `claim_id`: UUID

**Response 200:**
```json
{
  "claim_type": "risk",
  "claim_id": "r-001-...",
  "evidence": [
    {
      "id": "ev-001-...",
      "source_type": "commit",
      "source_id": "c-abc123-...",
      "document_title": null,
      "excerpt": "Fix reconciliation edge case in netting engine",
      "inference_type": "direct",
      "confidence": 0.91,
      "created_at": "2024-06-01T10:30:00Z"
    }
  ],
  "total_count": 47
}
```

---

## 15. Audit Log Endpoint

### `GET /api/v1/audit`

Retrieve audit log entries.

**Required role:** Admin

**Query Parameters:**
- `user_id`: filter by user
- `operation`: `create | read | update | delete | export`
- `entity_type`: filter by entity type
- `from_date`, `to_date`: ISO 8601 timestamps
- `page`, `page_size`

**Response 200:** Paginated audit log entries.

---

## 16. Endpoint Summary

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | `/health` | None | Health check |
| POST | `/api/v1/auth/token` | None | Login |
| POST | `/api/v1/auth/refresh` | None | Refresh token |
| POST | `/api/v1/auth/logout` | Any | Logout |
| GET | `/api/v1/analytics` | Viewer | System statistics |
| POST | `/api/v1/ingestion/upload` | Analyst | Upload single document |
| POST | `/api/v1/ingestion/bulk` | Admin | Bulk upload |
| GET | `/api/v1/ingestion/jobs` | Analyst | List ingestion jobs |
| GET | `/api/v1/ingestion/jobs/{id}` | Analyst | Job detail |
| GET | `/api/v1/knowledge` | Viewer | List knowledge areas |
| GET | `/api/v1/knowledge/{id}` | Viewer | Knowledge area detail |
| GET | `/api/v1/risks` | Viewer | List risk scores |
| GET | `/api/v1/risks/{id}` | Viewer | Risk detail with evidence |
| GET | `/api/v1/people` | Viewer | List people |
| GET | `/api/v1/people/{id}` | Viewer | Person profile |
| GET | `/api/v1/systems` | Viewer | List services |
| GET | `/api/v1/systems/{id}` | Viewer | Service profile |
| GET | `/api/v1/graph` | Viewer | Graph subgraph |
| POST | `/api/v1/simulation` | Analyst | Run what-if simulation |
| GET | `/api/v1/recommendations` | Viewer | List recommendations |
| GET | `/api/v1/recommendations/{id}` | Viewer | Recommendation detail |
| PATCH | `/api/v1/recommendations/{id}/status` | Analyst | Update status |
| POST | `/api/v1/query` | Viewer | AI assistant query |
| GET | `/api/v1/users` | Admin | List users |
| POST | `/api/v1/users` | Admin | Create user |
| PATCH | `/api/v1/users/{id}` | Admin | Update user |
| DELETE | `/api/v1/users/{id}` | Admin | Deactivate user |
| GET | `/api/v1/evidence/{type}/{id}` | Viewer | Evidence records |
| GET | `/api/v1/audit` | Admin | Audit log |
