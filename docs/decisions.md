# MemoryLeak — Architectural Decision Records

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Last Updated:** 2026-09-03

---

## ADR Format

Each record follows this structure:

```
ID:         ADR-NNN
Title:      Short, present-tense description
Status:     Proposed | Accepted | Superseded | Deprecated
Date:       YYYY-MM-DD
Problem:    What decision needed to be made
Options:    What was considered
Decision:   What was chosen
Rationale:  Why this was chosen
Tradeoffs:  What is sacrificed
Consequences: What this implies going forward
```

---

## ADR-001: Python as Backend Language

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a backend programming language for the MemoryLeak server.

**Options:**
1. Python
2. Node.js / TypeScript
3. Go
4. Java / Kotlin

**Decision:** Python

**Rationale:**
- The NLP and ML ecosystem (spaCy, sentence-transformers, scikit-learn, numpy) is Python-native. Using Python eliminates inter-language FFI overhead and avoids wrapping Python models in a service just to serve them from another language.
- FastAPI provides an async, type-annotated web framework with automatic OpenAPI generation.
- The target audience (researchers, ML engineers) is most fluent in Python.
- Reproducibility of NLP pipelines is significantly easier in Python.

**Tradeoffs:**
- Python has higher per-request overhead than Go or compiled languages.
- GIL limits true threading parallelism (mitigated by async I/O and background workers).

**Consequences:**
- All backend code is Python 3.11+.
- NLP models run in-process during development; may be extracted to a worker in production.
- Type hints with Pydantic v2 are required for all schemas.

---

## ADR-002: FastAPI as Web Framework

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a Python web framework.

**Options:**
1. FastAPI
2. Django REST Framework
3. Flask
4. Litestar

**Decision:** FastAPI

**Rationale:**
- Native async support (asyncio) for I/O-bound operations.
- Pydantic v2 integration provides schema validation and serialization with minimal boilerplate.
- Automatic OpenAPI/Swagger documentation generation.
- Strong typing throughout the codebase.
- Lightweight — does not impose ORM or admin panel.

**Tradeoffs:**
- Django has a richer admin interface and more mature auth ecosystem.
- FastAPI is newer; some ecosystem packages are less mature.

**Consequences:**
- All endpoints defined with async def where appropriate.
- Pydantic schemas define all request and response models.
- JWT-based auth must be implemented manually (no built-in session system).

---

## ADR-003: PostgreSQL as Relational Database

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a relational database for core application data.

**Options:**
1. PostgreSQL
2. MySQL / MariaDB
3. SQLite (dev only)

**Decision:** PostgreSQL 16

**Rationale:**
- pgvector extension enables vector similarity search within PostgreSQL, avoiding a separate vector database for MVP.
- Full SQL compliance, JSONB support, and excellent indexing options.
- ACID compliance and transactional integrity.
- Well-supported by SQLAlchemy 2.0.
- ARRAY and JSONB types simplify storing evidence IDs and contributing factors.

**Tradeoffs:**
- Heavier than SQLite for development.
- MySQL lacks pgvector.

**Consequences:**
- PostgreSQL must always be running via Docker Compose.
- SQLite may be used for isolated unit testing of repository logic with SQLAlchemy's create_engine().
- All migrations managed via Alembic.

---

## ADR-004: pgvector for Vector Storage

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a vector storage solution for chunk embeddings.

**Options:**
1. pgvector (PostgreSQL extension)
2. Weaviate (dedicated vector database)
3. Qdrant
4. Pinecone (cloud)
5. ChromaDB (embedded)

**Decision:** pgvector within PostgreSQL

**Rationale:**
- Eliminates a separate service in the Docker Compose stack for the MVP.
- Keeps the data co-located with relational metadata — joins between embeddings and document metadata work natively.
- Sufficient for MVP scale (≤ 500k chunks).
- Avoids dependency on cloud services, preserving reproducibility.
- IVFFlat index provides acceptable approximate nearest neighbor performance at MVP scale.

**Tradeoffs:**
- At very large scale (millions of vectors), dedicated vector databases offer better query performance and scalability.
- pgvector's approximate nearest neighbor is less optimized than HNSW in dedicated stores.

**Consequences:**
- Vector search is done within PostgreSQL via SQL queries.
- IVFFlat index is created after bulk data load, not during incremental ingestion.
- If scale exceeds 1M vectors, revisit this decision (see ADR-004-R1 when applicable).

---

## ADR-005: Neo4j as Graph Database

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a graph database for the knowledge graph.

**Options:**
1. Neo4j Community Edition
2. Amazon Neptune
3. ArangoDB
4. PostgreSQL with recursive CTEs (no separate graph DB)
5. NetworkX (in-memory, Python)

**Decision:** Neo4j 5.x Community Edition

**Rationale:**
- Industry-standard property graph database.
- Cypher query language is expressive for the traversal patterns required (dependency chains, expertise paths, bus-factor queries).
- Strong visualization ecosystem (Neo4j Bloom, or custom D3-based frontend).
- Official Python driver (`neo4j`) is mature and async-capable.
- Community Edition is free and Docker-compatible.

**Tradeoffs:**
- Community Edition lacks enterprise features (clustering, RBAC at DB level).
- Adds a third service to Docker Compose.
- Cypher is not SQL; team must learn it.

**Consequences:**
- Neo4j runs as a Docker service alongside PostgreSQL.
- The graph is maintained as a materialized view of the relational data — PostgreSQL is the system of record; Neo4j is derived.
- Graph updates happen via background synchronization after ingestion.
- Complex cross-store joins (relational + graph) are resolved at the service layer, not at the database level.

---

## ADR-006: sentence-transformers for Embeddings

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose an embedding model for document chunk vectorization.

**Options:**
1. sentence-transformers / all-MiniLM-L6-v2 (local)
2. OpenAI text-embedding-3-small (API)
3. Cohere Embed (API)
4. E5 / BGE models (local)
5. FastText (word-level, no context)

**Decision:** `sentence-transformers` with `all-MiniLM-L6-v2` as default

**Rationale:**
- Runs entirely locally — no API costs, no external dependencies, fully reproducible.
- `all-MiniLM-L6-v2` produces 384-dimensional embeddings with strong semantic quality for its size.
- Critical for research reproducibility: embedding results are deterministic and do not change between runs.
- Can be swapped to a larger model (e.g., `all-mpnet-base-v2`, `e5-base-v2`) via configuration.

**Tradeoffs:**
- Lower semantic quality than OpenAI's latest embedding models.
- Requires model download on first run (~90MB for all-MiniLM-L6-v2).
- Inference is slower than API calls at large scale (mitigated by batching).

**Consequences:**
- Model name and version are stored with every embedding in `chunk_embeddings.model_name` and `model_version`.
- Model can be swapped via environment variable `EMBEDDING_MODEL`.
- If model changes, existing embeddings must be recomputed — flagged as a migration concern.

---

## ADR-007: Modular Monolith Architecture

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Determine the service decomposition strategy for the backend.

**Options:**
1. Modular monolith (single FastAPI app, internal module boundaries)
2. Microservices (separate services for ingestion, intelligence, API)
3. Monolith (no module boundaries)

**Decision:** Modular monolith

**Rationale:**
- MVP scale does not justify microservice operational overhead.
- Microservices require service discovery, inter-service auth, distributed tracing, and distributed data consistency — all complexity not justified at this stage.
- A modular monolith with clear internal boundaries (ingestion/, intelligence/, api/) provides the same architectural clarity and is easier to extract later if needed.
- Aligns with the "no premature advanced infrastructure" principle.

**Tradeoffs:**
- Cannot independently scale ingestion vs. query serving.
- All modules share process memory; a memory leak in ingestion affects the API.

**Consequences:**
- The backend is a single FastAPI application.
- Internal modules are enforced by directory structure and import discipline (modules should not cross-import).
- Future extraction into services is possible by defining explicit service interfaces from day one.

---

## ADR-008: Next.js for Frontend

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a frontend framework.

**Options:**
1. Next.js (React, SSR/SSG capable)
2. Vite + React SPA
3. Vue.js + Nuxt
4. Svelte / SvelteKit

**Decision:** Next.js 14 with App Router

**Rationale:**
- Strong ecosystem for data-heavy dashboards.
- Server Components allow efficient data fetching close to the data source.
- TypeScript support is first-class.
- Large component ecosystem (charts, graph visualization).
- Consistent with the technology baseline.

**Tradeoffs:**
- SSR adds complexity for highly interactive graph visualizations (client-only rendering required for some components).
- More opinionated than a plain SPA.

**Consequences:**
- Frontend is in the `frontend/` directory.
- API calls go through Next.js server actions or client-side fetch to the FastAPI backend.
- Graph visualization components are client-only (no SSR).

---

## ADR-009: Docker Compose for Local Infrastructure

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a local development and deployment strategy.

**Options:**
1. Docker Compose (multi-container local orchestration)
2. Kubernetes (k3s locally)
3. Manual process management (no containers)
4. Cloud-hosted services (RDS, Neptune)

**Decision:** Docker Compose

**Rationale:**
- Fully reproducible local environment: `docker compose up` starts everything.
- No cloud dependency — critical for reproducibility in a research context.
- Simpler than Kubernetes for a single-node research prototype.
- Every developer and evaluator can run the full stack locally.

**Tradeoffs:**
- Not production-grade orchestration.
- Multi-host scaling requires migration to Kubernetes or a managed service.

**Consequences:**
- `docker-compose.yml` defines: PostgreSQL, Neo4j, backend, frontend.
- All configuration via `.env` file (never committed).
- Volume mounts preserve database state between restarts.

---

## ADR-010: JWT Authentication

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose an authentication mechanism for the API.

**Options:**
1. JWT (stateless, in-header)
2. Session cookies (stateful, server-side)
3. OAuth2 with external provider
4. API keys only

**Decision:** JWT Bearer tokens with refresh token support

**Rationale:**
- Stateless — no session store required for MVP.
- Standard for REST APIs consumed by a frontend SPA.
- Works cleanly with FastAPI's OAuth2PasswordBearer dependency injection.
- Sufficient for a single-organization research prototype.

**Tradeoffs:**
- Token revocation requires a blocklist (not implemented in MVP — logged tokens are valid until expiry).
- Short-lived access tokens (15 min) with refresh tokens mitigate revocation gap.

**Consequences:**
- Access token TTL: 15 minutes. Refresh token TTL: 7 days.
- `SECRET_KEY` must be set via environment variable.
- All endpoints (except `/health` and `/auth/token`) require a valid JWT.

---

## ADR-011: spaCy + Rule-based Hybrid for NLP

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose an NLP approach for entity and relationship extraction.

**Options:**
1. Pure spaCy NER (statistical model)
2. Rule-based only (regex + patterns)
3. LLM-only extraction (GPT-4 / Claude)
4. Hybrid: spaCy statistical + rule-based patterns + confidence scoring

**Decision:** Hybrid: spaCy statistical NER + custom rule-based patterns

**Rationale:**
- Pure LLM extraction is expensive, non-deterministic, and not reproducible at scale.
- Pure rule-based is brittle for organizational entity names.
- spaCy's `en_core_web_sm` or `en_core_web_trf` provides a strong base NER.
- Custom `EntityRuler` patterns handle organization-specific terms (service names, technology names from the synthetic data schema).
- Confidence estimation is possible by combining spaCy's scores with rule match certainty.
- This hybrid approach aligns with the research hypothesis (Section 4 in research-methodology.md).

**Tradeoffs:**
- Requires manual curation of domain-specific patterns.
- spaCy's transformer model (`en_core_web_trf`) is large (~450MB); the small model may miss subtle entities.

**Consequences:**
- NLP pipeline is in `backend/app/intelligence/nlp/`.
- Model choice (`SPACY_MODEL`) is configurable via environment variable.
- All extractions carry a confidence score.
- LLM is reserved for Phase 10 (RAG assistant) — not used in core extraction.

---

## ADR-012: SQLAlchemy 2.0 ORM

**Status:** Accepted
**Date:** 2026-09-03

**Problem:** Choose a database access strategy for the Python backend.

**Options:**
1. SQLAlchemy 2.0 ORM + Core
2. Raw SQL (psycopg2 / asyncpg)
3. SQLModel (SQLAlchemy + Pydantic)
4. Tortoise ORM (async-native)

**Decision:** SQLAlchemy 2.0 with async support (asyncpg driver)

**Rationale:**
- SQLAlchemy 2.0 has a clean async API.
- ORM provides type safety and migration support via Alembic.
- Repository pattern over raw ORM prevents business logic from leaking into database queries.
- SQLAlchemy Core available for complex queries where ORM overhead is undesirable.

**Tradeoffs:**
- More boilerplate than raw SQL.
- ORM queries can generate inefficient SQL if not careful (N+1 queries).

**Consequences:**
- All database access goes through the repository layer.
- Alembic manages migrations — no raw `CREATE TABLE` in application code.
- `asyncpg` is the driver; the connection string uses `postgresql+asyncpg://`.
