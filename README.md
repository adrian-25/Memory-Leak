# MemoryLeak

**AI-Powered Organizational Knowledge Risk and Dependency Intelligence Platform**

---

MemoryLeak analyzes organizational knowledge sources — code repositories, documents, issues, commits, and discussions — to identify knowledge concentration risks, single-person dependencies, documentation gaps, and knowledge-loss scenarios before they become organizational crises.

---

## What It Does

- Detects **bus-factor risks**: services or knowledge areas known by only one person
- Measures **knowledge concentration**: who knows what, how much, and with what evidence
- Surfaces **documentation gaps**: undocumented, stale, or conflicting documentation
- Generates **evidence-backed recommendations**: specific, prioritized, actionable
- Runs **what-if simulations**: what happens to organizational knowledge if someone leaves?
- Provides an **AI assistant**: ask questions about your organization's knowledge, grounded in real evidence

---

## Current Status

**Phase 0 — Planning: Complete**

All architecture, requirements, data model, API contracts, research methodology, and development roadmap are documented in `docs/`.

**Phase 1 — Infrastructure: Not started**

See `docs/project-memory.md` for the exact current state and next steps.

---

## Documentation

| Document | Description |
|---|---|
| `docs/project-memory.md` | Current project state — read this first when resuming development |
| `docs/requirements.md` | Functional and non-functional requirements |
| `docs/architecture.md` | System architecture, components, data flow |
| `docs/data-model.md` | PostgreSQL schema, Neo4j graph model, vector strategy |
| `docs/api-specification.md` | All API endpoints with request/response contracts |
| `docs/decisions.md` | Architectural Decision Records (ADRs) |
| `docs/research-methodology.md` | Research questions, hypotheses, evaluation plan |
| `docs/experiments.md` | Planned experiments and baselines |
| `docs/limitations.md` | Known limitations and ethical constraints |
| `docs/development-log.md` | Chronological development history |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ / FastAPI / SQLAlchemy 2.0 |
| Relational Database | PostgreSQL 16 + pgvector |
| Graph Database | Neo4j 5.x Community |
| NLP | spaCy 3.7+ |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Frontend | Next.js 14 / React 18 / TypeScript / Tailwind CSS |
| Infrastructure | Docker / Docker Compose |

---

## Quick Start (Phase 1+)

> These commands will work once Phase 1 infrastructure is implemented.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/memoryleak.git
cd memoryleak

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env and set passwords and secrets

# 3. Start all services
docker compose up -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Generate synthetic dataset
docker compose exec backend python scripts/generate_synthetic_data.py

# 6. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Neo4j Browser: http://localhost:7474
```

---

## Development Phases

| Phase | Description | Status |
|---|---|---|
| 0 | Planning and documentation | ✓ Complete |
| 1 | Infrastructure (Docker, DB, API skeleton) | Not started |
| 2 | Synthetic data engine | Not started |
| 3 | Ingestion pipeline | Not started |
| 4 | NLP + Embeddings | Not started |
| 5 | Knowledge graph | Not started |
| 6 | Intelligence engine (scoring) | Not started |
| 7 | Evidence system | Not started |
| 8 | Recommendations engine | Not started |
| 9 | Simulation engine | Not started |
| 10 | AI assistant (RAG) | Not started |
| 11 | Dashboard and visualization | Not started |
| 12 | Evaluation (baselines) | Not started |
| 13 | Ablation studies | Not started |
| 14 | Deployment preparation | Not started |

---

## Research Context

MemoryLeak is built as a research prototype investigating:

> Can a hybrid system combining semantic embeddings, NLP, knowledge graphs, and rule-based risk scoring reliably identify organizational knowledge concentration and knowledge-loss risks?

See `docs/research-methodology.md` for the full research design.

---

## Ethical Considerations

MemoryLeak analyzes organizational knowledge patterns, not individual performance. Risk scores indicate evidence-based organizational knowledge concentration, not employee performance or value.

**Risk scores must not be used for employment decisions.**

See `docs/limitations.md` for the full ethical constraints and responsible use guidance.

---

## License

MIT — see `LICENSE` for details.
