# MemoryLeak Project Memory

**IMPORTANT:** This file is the authoritative state of the MemoryLeak project. It must be read at the start of every development session. It must be updated after every two major development updates.

---

## Current Phase

**Phase 0 — Planning**
Status: COMPLETED ✓

## Current Milestone

Phase 0 complete. All planning documentation created and internally validated.
**Ready to begin Phase 1 — Infrastructure.**

## Overall Completion Estimate

**Phase 0:** 100% complete
**Phase 1 (Infrastructure):** 0% — not started
**Overall MVP:** ~7% (Phase 0 of 14 phases complete)

---

## What Has Been Completed

### Phase 0 — Planning (Complete)

All documentation files created:

- `docs/requirements.md`: 8 sections, 68 functional requirements (10 groups), 24 non-functional requirements (6 groups), out-of-scope items, dependency chain, MVP acceptance criteria.
- `docs/architecture.md`: Component diagrams for ingestion, intelligence, API, and frontend; data flow diagrams for ingestion, risk dashboard, and AI assistant; infrastructure layout (Docker Compose); security/RBAC matrix; observability signals; technology version baseline.
- `docs/data-model.md`: Full PostgreSQL schema (14 tables: organizations, users, raw_sources, documents, document_chunks, chunk_embeddings, people, teams, projects, services, knowledge_areas, commits, issues, discussions, expertise_scores, risk_scores, evidence_records, recommendations, audit_logs); Neo4j graph model (8 node labels, 15 relationship types, 4 key Cypher queries); pgvector strategy; temporal decay formula.
- `docs/api-specification.md`: 28 endpoints across 15 sections; full request/response JSON contracts; error format; pagination conventions; RBAC matrix.
- `docs/decisions.md`: 12 ADRs (ADR-001 through ADR-012) covering language, framework, databases, vector storage, graph DB, embeddings, architecture style, frontend, infrastructure, auth, NLP approach, ORM.
- `docs/research-methodology.md`: Central RQ, 5 sub-questions, 5 falsifiable hypotheses, experimental design overview, evaluation metrics (bus-factor F1/AUC, expertise NDCG, doc coverage F1, explanation faithfulness, retrieval recall), ethical constraints, reproducibility checklist.
- `docs/experiments.md`: 4 baselines (rule-based, embedding-only, LLM, graph analytics), proposed hybrid system, 4 ablations, 3 sensitivity analyses; evaluation scripts defined; results table empty until Phase 12.
- `docs/development-log.md`: Initial entry for Phase 0 completion.
- `docs/limitations.md`: 10 technical limitations, 4 research limitations, ethical constraints, prohibited uses, 5 open questions.
- `docs/project-memory.md`: This file.
- `README.md`: Project overview, quick-start instructions.
- `.gitignore`: Python, Node.js, Docker, IDE exclusions.
- `.env.example`: All required environment variables.
- `LICENSE`: MIT.

---

## What Is Currently Being Built

Nothing — Phase 0 complete. Awaiting start of Phase 1.

---

## What Remains

### Phase 1 — Infrastructure (next)
- [ ] Create full repository directory structure
- [ ] Write `docker-compose.yml` (PostgreSQL + pgvector, Neo4j, backend, frontend)
- [ ] Write per-service Dockerfiles (`docker/backend.Dockerfile`, `docker/frontend.Dockerfile`)
- [ ] Write `backend/app/main.py` — FastAPI app skeleton
- [ ] Configure structured logging in backend
- [ ] Write `backend/app/core/config.py` — settings from environment variables
- [ ] Write `.env` from `.env.example` (local dev)
- [ ] Run `docker compose up` and verify all services healthy
- [ ] Write a smoke-test script to verify PostgreSQL, pgvector, and Neo4j connectivity
- [ ] Write initial Alembic migration with core tables
- [ ] Write `frontend/` Next.js project scaffold
- [ ] Verify frontend can reach backend health endpoint

### Phases 2–14 — Not started

---

## Files Created

```
docs/
├── requirements.md           ✓
├── architecture.md           ✓
├── data-model.md             ✓
├── api-specification.md      ✓
├── decisions.md              ✓
├── research-methodology.md   ✓
├── experiments.md            ✓
├── development-log.md        ✓
├── limitations.md            ✓
└── project-memory.md         ✓
README.md                     ✓
.gitignore                    ✓
.env.example                  ✓
LICENSE                       ✓
```

---

## Files Modified

None — all files are newly created.

---

## Architecture Decisions

Finalized in Phase 0. See `docs/decisions.md` for full ADRs.

| ADR | Decision |
|---|---|
| ADR-001 | Python 3.11+ as backend language |
| ADR-002 | FastAPI as web framework |
| ADR-003 | PostgreSQL 16 as relational database |
| ADR-004 | pgvector within PostgreSQL for vector search |
| ADR-005 | Neo4j 5.x Community as graph database |
| ADR-006 | sentence-transformers / all-MiniLM-L6-v2 for embeddings |
| ADR-007 | Modular monolith backend architecture |
| ADR-008 | Next.js 14 for frontend |
| ADR-009 | Docker Compose for local infrastructure |
| ADR-010 | JWT Bearer tokens for authentication |
| ADR-011 | spaCy + rule-based hybrid for NLP |
| ADR-012 | SQLAlchemy 2.0 with async (asyncpg) |

---

## Database State

**PostgreSQL:** Not created. Schema defined in `docs/data-model.md`. Migrations pending Phase 1.
**Neo4j:** Not created. Graph model defined in `docs/data-model.md`.
**pgvector:** Not installed. Will be enabled as PostgreSQL extension in Phase 1.

---

## API State

28 endpoints designed in `docs/api-specification.md`. None implemented. Backend skeleton not yet created.

---

## Frontend State

Not started. Architecture defined in `docs/architecture.md` Section 3.4.

---

## Backend State

Not started. Directory structure defined in `docs/architecture.md` Section 2.

---

## AI/NLP State

Not started. Approach defined: spaCy + rule-based hybrid. See ADR-011.

---

## Knowledge Graph State

Not started. Graph model defined in `docs/data-model.md` Section 3.

---

## Risk Engine State

Not started. Scoring approach defined in requirements (F-RSK-01 through F-RSK-08).

---

## Testing State

No tests written. Testing strategy:
- Unit tests: `backend/tests/` — parsers, scoring, graph construction, risk calculations, retrieval
- Integration tests: `tests/integration/` — upload → parse → extract → embed → graph → risk → dashboard
- E2E tests: `tests/e2e/` — full user workflows

---

## Known Bugs

None — no code exists yet.

---

## Known Limitations

10 technical limitations documented in `docs/limitations.md`. Key items:

- LIM-TECH-01: Synthetic data only (no real org validation)
- LIM-TECH-02: English language only
- LIM-TECH-06: Expertise scores are evidence-based proxies (not direct knowledge measurement)
- LIM-TECH-10: Risk weights not empirically calibrated

---

## Technical Debt

None — no code exists yet.

---

## Experiments Completed

None — experiments begin in Phase 12.

---

## Experiments Pending

All 12 planned experiments (EXP-B1 through EXP-A4) are PLANNED status. See `docs/experiments.md`.

---

## Important Decisions

1. The ground-truth labels for the synthetic dataset MUST be sealed in `data/evaluation/` and MUST NOT be accessible to the inference pipeline at any point.
2. pgvector IVFFlat index must be created AFTER bulk data load, not during incremental ingestion.
3. Neo4j is a derived view — PostgreSQL is the system of record.
4. All risk scores must expose evidence, contributing factors, and confidence.
5. Simulation output must always carry the `WARNING: SIMULATION / ESTIMATE` label.
6. No LLM calls in the core extraction pipeline — LLM is reserved for Phase 10 RAG assistant.

---

## Things That MUST NOT Be Changed

1. Ground-truth label files in `data/evaluation/` — sealed once generated in Phase 2
2. Random seed used for synthetic data generation (`RANDOM_SEED=42`)
3. The evaluation fairness constraints (all systems use identical input data)
4. The evidence chain requirement — no risk score without traceable evidence

---

## Next Exact Step

**Phase 1 — Step 1: Repository Structure**

1. Create the full directory structure defined in `docs/architecture.md` Section 2.
2. Create `docker-compose.yml` with four services: postgres, neo4j, backend, frontend.
3. Create `docker/backend.Dockerfile` and `docker/frontend.Dockerfile`.
4. Create `backend/app/main.py` — minimal FastAPI skeleton with `/health` endpoint.
5. Create `backend/app/core/config.py` — Pydantic Settings reading from environment variables.
6. Create `backend/requirements.txt` — all pinned dependencies.
7. Run `docker compose up` and verify all services start without errors.
8. Write and run a connectivity smoke test (Python script that verifies PostgreSQL, pgvector, and Neo4j).
9. Create initial Alembic migration for the PostgreSQL schema.
10. Create Next.js frontend scaffold.

---

## Recommended Next Session Prompt

```
Continue MemoryLeak development. Read docs/project-memory.md first.
Phase 0 is complete — all planning documentation exists.
Begin Phase 1: Infrastructure.
Start from "Next Exact Step" in project-memory.md.
Do not recreate Phase 0 documentation.
```

---

## Last Updated

2026-09-03 — Phase 0 complete. AI Agent (Kiro).
