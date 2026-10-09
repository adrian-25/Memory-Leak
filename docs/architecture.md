# MemoryLeak — System Architecture

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Last Updated:** 2026-09-03

---

## 1. Architecture Overview

MemoryLeak follows a modular monorepo architecture with a clear separation between ingestion, intelligence, and interface layers. The system is designed as a single-server deployment for the MVP, fully containerized with Docker Compose.

```
┌─────────────────────────────────────────────────────────────────┐
│                        MEMORYLEAK PLATFORM                       │
│                                                                  │
│  ┌────────────┐    ┌──────────────────┐    ┌────────────────┐   │
│  │  FRONTEND  │    │     BACKEND      │    │  DATA STORES   │   │
│  │  Next.js   │◄──►│    FastAPI       │◄──►│  PostgreSQL    │   │
│  │  React     │    │    Python        │    │  + pgvector    │   │
│  │  TypeScript│    │                  │    │  Neo4j         │   │
│  └────────────┘    └──────────────────┘    └────────────────┘   │
│                              │                                   │
│                    ┌─────────┴──────────┐                        │
│                    │                    │                        │
│              ┌─────▼─────┐    ┌────────▼────────┐              │
│              │ INGESTION  │    │  INTELLIGENCE   │              │
│              │ Pipeline   │    │  Engine         │              │
│              └───────────┘    └─────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Repository Structure

```
memoryleak/
│
├── frontend/                    # Next.js application
│   ├── app/                     # App router pages
│   ├── components/              # Reusable UI components
│   ├── features/                # Feature-scoped modules
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # Utility libraries
│   ├── services/                # API client services
│   ├── types/                   # TypeScript type definitions
│   └── tests/                   # Frontend tests
│
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI route handlers
│   │   ├── core/                # Configuration, logging, security
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── repositories/        # Database access layer
│   │   ├── services/            # Business logic layer
│   │   ├── intelligence/        # AI/ML subsystems
│   │   │   ├── nlp/             # NLP pipeline
│   │   │   ├── embeddings/      # Embedding generation
│   │   │   ├── graph/           # Graph construction and queries
│   │   │   ├── risk/            # Risk scoring engine
│   │   │   ├── recommendations/ # Recommendations engine
│   │   │   ├── simulation/      # What-if simulation
│   │   │   └── retrieval/       # Hybrid retrieval (RAG)
│   │   ├── ingestion/           # Document parsing pipeline
│   │   ├── security/            # Auth, RBAC, audit logging
│   │   ├── observability/       # Structured logging, metrics
│   │   └── main.py              # FastAPI app entrypoint
│   └── tests/                   # Backend unit and integration tests
│
├── data/
│   ├── raw/                     # Raw input files
│   ├── synthetic/               # Generated synthetic datasets
│   ├── processed/               # Cleaned/chunked data
│   ├── schemas/                 # Data schema definitions
│   └── evaluation/              # Ground-truth labels for evaluation
│
├── experiments/
│   ├── baselines/               # Baseline system implementations
│   ├── ablations/               # Ablation study configurations
│   ├── evaluation/              # Evaluation scripts
│   └── results/                 # Stored experiment results
│
├── scripts/                     # CLI scripts (data gen, migrations, etc.)
├── tests/
│   ├── integration/             # Cross-service integration tests
│   └── e2e/                     # End-to-end workflow tests
│
├── docs/                        # All documentation
├── docker/                      # Per-service Dockerfiles
├── docker-compose.yml
├── README.md
├── .env.example
├── .gitignore
└── LICENSE
```

---

## 3. Component Architecture

### 3.1 Ingestion Pipeline

```
Raw Source File
      │
      ▼
┌─────────────┐
│   Parser    │  PDF, DOCX, Markdown, TXT, Python, JS/TS, Java, SQL,
│             │  YAML/JSON/TOML/INI, Issues JSON, Commits JSON
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Cleaner   │  Normalize whitespace, strip non-content, deduplicate
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Chunker   │  Sliding window with overlap, code-aware chunking
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Metadata         │  Extract author, timestamp, source path,
│ Extraction       │  content hash, document type
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Entity           │  Person, Team, Project, Technology, Service,
│ Extraction       │  KnowledgeArea — spaCy + rule-based hybrid
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Embedding        │  sentence-transformers model
│ Generation       │  per chunk → pgvector storage
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Knowledge        │  Relationship extraction → Neo4j graph update
│ Extraction       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Storage         │  PostgreSQL (documents, chunks, metadata, embeddings)
│                  │  Neo4j (entities, relationships)
└──────────────────┘
```

### 3.2 Intelligence Engine

```
┌─────────────────────────────────────────────────────────┐
│                   INTELLIGENCE ENGINE                    │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Expertise  │  │ Concentration│  │ Documentation │  │
│  │  Scoring    │  │ Analysis     │  │ Coverage      │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          │                              │
│                          ▼                              │
│              ┌───────────────────────┐                  │
│              │    Risk Aggregator    │                  │
│              │  (explainable score)  │                  │
│              └───────────┬───────────┘                  │
│                          │                              │
│            ┌─────────────┼─────────────┐               │
│            ▼             ▼             ▼               │
│      ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│      │Recomm.   │  │Simulation│  │Evidence  │         │
│      │Engine    │  │Engine    │  │Store     │         │
│      └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────┘
```

### 3.3 API Layer

```
HTTP Request
     │
     ▼
FastAPI Router
     │
     ▼
Auth Middleware  →  JWT validation, RBAC check
     │
     ▼
Request Validator  →  Pydantic schema validation
     │
     ▼
Service Layer  →  Business logic, orchestration
     │
     ├──► Repository Layer  →  PostgreSQL via SQLAlchemy
     ├──► Graph Layer       →  Neo4j via neo4j-driver
     └──► Intelligence      →  NLP, embeddings, scoring
```

### 3.4 Frontend Architecture

```
┌─────────────────────────────────────┐
│         Next.js App Router          │
│                                     │
│  ┌─────────┐  ┌────────────────┐   │
│  │ Pages   │  │  API Client    │   │
│  │         │  │  (services/)   │   │
│  └────┬────┘  └───────┬────────┘   │
│       │               │            │
│       ▼               ▼            │
│  ┌──────────────────────────────┐  │
│  │   Feature Modules            │  │
│  │   - Dashboard                │  │
│  │   - Risk Explorer            │  │
│  │   - Graph Explorer           │  │
│  │   - Documentation Gaps       │  │
│  │   - Person Profile           │  │
│  │   - System Profile           │  │
│  │   - AI Assistant             │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Shared Components          │  │
│  │   - RiskBadge                │  │
│  │   - EvidencePanel            │  │
│  │   - GraphCanvas              │  │
│  │   - ScoreCard                │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## 4. Data Flow

### 4.1 Core Ingestion Flow

```
Raw Source
    ↓  (Parser selects by file type)
Parser (PDF/DOCX/MD/Code/Issue/Commit)
    ↓
Cleaner (normalize, sanitize)
    ↓
Chunker (split with metadata)
    ↓
Metadata Extraction (author, date, hash, type)
    ↓
Entity Extraction (NER + rules → confidence)
    ↓
Embedding Generation (sentence-transformers)
    ↓
Knowledge Extraction (relationship inference)
    ↓
PostgreSQL (raw_documents, document_chunks, entities)
    ↓  (background job)
pgvector (chunk_embeddings table)
    ↓  (background job)
Neo4j (entity nodes + relationship edges)
```

### 4.2 Query Flow (Risk Dashboard)

```
Dashboard Request
    ↓
API: GET /api/v1/risks
    ↓
RiskService.get_risks(filters)
    ↓
RiskRepository → PostgreSQL (pre-computed scores)
    ↓
EvidenceRepository → PostgreSQL (evidence records)
    ↓
Response: RiskScore + Evidence + Explanation
```

### 4.3 Query Flow (AI Assistant)

```
User Query
    ↓
API: POST /api/v1/query
    ↓
QueryService.process(query)
    ↓
┌──────────────────────────────────────────┐
│  Parallel Retrieval                       │
│  ├─ VectorSearch (pgvector) → chunks      │
│  ├─ GraphSearch (Neo4j) → entities/paths  │
│  └─ MetadataFilter → relevant docs        │
└──────────────────────────────────────────┘
    ↓
EvidenceAggregator (rank + merge results)
    ↓
LLM (with retrieved evidence as context)
    ↓
GroundedAnswer (answer + citations)
```

---

## 5. Infrastructure Architecture

```
docker-compose.yml
│
├── memoryleak-backend      (Python FastAPI, port 8000)
│   └── depends_on: postgres, neo4j
│
├── memoryleak-frontend     (Next.js, port 3000)
│   └── depends_on: backend
│
├── postgres                (PostgreSQL 16 + pgvector, port 5432)
│   └── volume: postgres_data
│
└── neo4j                   (Neo4j 5.x Community, port 7474/7687)
    └── volume: neo4j_data
```

All services communicate over an internal Docker network.
The frontend communicates with the backend exclusively via the REST API.
The backend communicates with PostgreSQL via SQLAlchemy and with Neo4j via the official Python driver.

---

## 6. Security Architecture

```
External Request
      │
      ▼
TLS Termination (production only)
      │
      ▼
FastAPI Auth Middleware
      │
      ├── JWT Token Validation
      ├── Token Expiry Check
      └── RBAC Permission Check
                │
                ▼
           Request Handler
                │
                ▼
         Audit Logger (every mutation logged)
```

### Role Permissions Matrix

| Capability | Admin | Analyst | Viewer |
|---|---|---|---|
| Upload documents | ✓ | ✓ | ✗ |
| Trigger ingestion | ✓ | ✓ | ✗ |
| View risk scores | ✓ | ✓ | ✓ |
| View evidence | ✓ | ✓ | ✓ |
| View graph | ✓ | ✓ | ✓ |
| Run simulation | ✓ | ✓ | ✗ |
| Manage users | ✓ | ✗ | ✗ |
| Delete data | ✓ | ✗ | ✗ |
| View audit log | ✓ | ✗ | ✗ |
| Export data | ✓ | ✓ | ✗ |

---

## 7. Observability Architecture

All backend services emit structured JSON logs (via Python `structlog` or `logging` with JSON formatter).

Tracked signals:

| Signal | Type | Detail |
|---|---|---|
| api_request | event | method, path, status, latency_ms, user_id |
| ingestion_job | event | source_type, doc_count, duration_ms, errors |
| ingestion_failure | error | doc_id, source_path, error_message |
| embedding_generation | event | chunk_count, model, duration_ms |
| graph_query | event | query_type, result_count, duration_ms |
| vector_search | event | query_id, top_k, latency_ms |
| risk_computation | event | entity_type, entity_id, score, duration_ms |
| ai_query | event | query_id, retrieval_count, llm_tokens, latency_ms |
| auth_failure | warning | reason, ip_address |
| audit_mutation | audit | user_id, operation, entity_type, entity_id |

---

## 8. Key Architectural Decisions (Summary)

Full ADRs are in `docs/decisions.md`. Summaries:

| Decision | Choice | Rationale |
|---|---|---|
| Backend language | Python | NLP/ML ecosystem dominance |
| Backend framework | FastAPI | Async, type-safe, fast |
| Relational DB | PostgreSQL | Reliable, pgvector extension available |
| Vector storage | pgvector | Avoids separate vector DB for MVP |
| Graph DB | Neo4j | Industry standard, Cypher is expressive |
| Embedding model | sentence-transformers | Local, reproducible, no API cost |
| Frontend | Next.js | SSR, strong ecosystem |
| Deployment | Docker Compose | Single-machine, reproducible |
| Architecture style | Modular monolith | Avoids microservice complexity for MVP |

---

## 9. Scalability Considerations (Post-MVP)

The current architecture does not require horizontal scaling for the MVP research prototype. However, the modular design permits future evolution:

- Ingestion pipeline can be extracted to a worker queue (Celery + Redis)
- Intelligence engine can be separated as async background jobs
- pgvector can be replaced with a dedicated vector store (Weaviate, Qdrant) if scale demands
- The backend can be split into microservices along the ingestion/intelligence/API boundaries
- Frontend can be deployed to a CDN

These are explicitly NOT in scope for the MVP.

---

## 10. Technology Versions (Baseline)

| Component | Technology | Version (minimum) |
|---|---|---|
| Backend language | Python | 3.11+ |
| Web framework | FastAPI | 0.111+ |
| ORM | SQLAlchemy | 2.0+ |
| Data validation | Pydantic | 2.x |
| Database | PostgreSQL | 16+ |
| Vector extension | pgvector | 0.7+ |
| Graph database | Neo4j | 5.x |
| NLP | spaCy | 3.7+ |
| Embeddings | sentence-transformers | 2.x |
| Frontend | Next.js | 14+ |
| UI | React | 18+ |
| Styling | Tailwind CSS | 3.x |
| Containerization | Docker | 24+ |
| Orchestration | Docker Compose | 2.x |
