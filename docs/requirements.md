# MemoryLeak — Requirements

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Last Updated:** 2026-09-03

---

## 1. Purpose

MemoryLeak is an AI-powered organizational knowledge risk and dependency intelligence platform. It analyzes organizational knowledge sources — code repositories, documents, issues, tickets, discussions, and communications — to identify:

- Knowledge concentration and single-person dependencies
- Documentation gaps and staleness
- Dependency and bus-factor risks
- Knowledge fragmentation across teams and systems
- Documentation/code drift
- Knowledge-transfer opportunities and organizational knowledge-loss scenarios

The system is designed as a serious research prototype that can evolve into an enterprise product.

---

## 2. Stakeholders

| Stakeholder | Role | Primary Concern |
|---|---|---|
| Engineering Leadership | Consumer | Bus-factor risk, succession planning |
| Knowledge Manager / Analyst | Operator | Documentation coverage, knowledge health |
| HR / People Ops | Consumer | Employee transition risk, offboarding |
| Individual Contributor | Consumer | Own knowledge profile, recommendations |
| System Administrator | Operator | Data ingestion, security, access control |
| Researcher | Evaluator | Evaluation methodology, experimental comparison |

---

## 3. Functional Requirements

### 3.1 Data Ingestion

| ID | Requirement |
|---|---|
| F-ING-01 | The system SHALL accept document uploads in PDF, DOCX, Markdown, and TXT formats. |
| F-ING-02 | The system SHALL parse source code in Python, JavaScript/TypeScript, Java, and SQL. |
| F-ING-03 | The system SHALL ingest configuration files (YAML, JSON, TOML, INI). |
| F-ING-04 | The system SHALL ingest structured issue/ticket data (JSON export format). |
| F-ING-05 | The system SHALL ingest commit history (JSON or structured text export). |
| F-ING-06 | The system SHALL ingest discussion/comment threads (JSON export format). |
| F-ING-07 | Every ingested record SHALL preserve provenance: source file, author, timestamp, content hash. |
| F-ING-08 | Duplicate documents SHALL be detected by content hash and flagged, not silently overwritten. |
| F-ING-09 | Ingestion failures SHALL be logged with the specific error and the affected record. |
| F-ING-10 | The system SHALL support bulk ingestion via the API. |

### 3.2 Entity and Knowledge Extraction

| ID | Requirement |
|---|---|
| F-EXT-01 | The system SHALL extract named entities: Person, Team, Project, Technology, System/Service, Knowledge Area. |
| F-EXT-02 | The system SHALL extract relationships: AUTHORED, CONTRIBUTED_TO, KNOWS, DEPENDS_ON, DESCRIBES, OWNS, RESOLVED. |
| F-EXT-03 | The system SHALL assign a confidence score (0.0–1.0) to every extracted entity and relationship. |
| F-EXT-04 | The system SHALL generate semantic embeddings for all document chunks. |
| F-EXT-05 | The system SHALL extract temporal metadata: creation date, last modified date, last referenced date. |
| F-EXT-06 | The system SHALL extract knowledge areas from code, documentation, and issues. |
| F-EXT-07 | Every extracted claim SHALL reference its source evidence (document ID + chunk ID + span offset). |

### 3.3 Knowledge Graph

| ID | Requirement |
|---|---|
| F-KG-01 | The system SHALL maintain a knowledge graph in Neo4j using the defined domain model. |
| F-KG-02 | The graph SHALL be queryable by person, team, project, service, and knowledge area. |
| F-KG-03 | The system SHALL support graph traversal queries: "What systems depend on Person X's knowledge?" |
| F-KG-04 | The system SHALL support shortest-path queries between entities. |
| F-KG-05 | The knowledge graph SHALL be updated incrementally upon new ingestion. |
| F-KG-06 | The system SHALL expose graph data via a structured API for visualization. |

### 3.4 Intelligence Engine — Expertise Scoring

| ID | Requirement |
|---|---|
| F-INT-01 | The system SHALL compute an expertise score for each (Person, KnowledgeArea) pair. |
| F-INT-02 | Expertise scores SHALL be derived from: commit frequency, authorship, issue resolution, documentation authorship, discussion depth. |
| F-INT-03 | The system SHALL compute a recency-weighted expertise score that penalizes stale contributions. |
| F-INT-04 | All expertise scores SHALL expose their contributing evidence. |

### 3.5 Intelligence Engine — Risk Scoring

| ID | Requirement |
|---|---|
| F-RSK-01 | The system SHALL compute a bus-factor score for every Service, Project, and KnowledgeArea. |
| F-RSK-02 | The system SHALL compute a knowledge-concentration score for every KnowledgeArea. |
| F-RSK-03 | The system SHALL compute a documentation-coverage score for every Service and Project. |
| F-RSK-04 | The system SHALL compute a documentation-staleness score. |
| F-RSK-05 | The system SHALL compute a documentation/code-drift score. |
| F-RSK-06 | The system SHALL compute an overall organizational risk index. |
| F-RSK-07 | Every risk score SHALL expose: score value, contributing factors, evidence references, confidence, known limitations. |
| F-RSK-08 | Risk scores SHALL be categorized by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO. |

### 3.6 Recommendations Engine

| ID | Requirement |
|---|---|
| F-REC-01 | The system SHALL generate documentation recommendations for undocumented or stale knowledge areas. |
| F-REC-02 | The system SHALL recommend backup experts for high-concentration knowledge areas. |
| F-REC-03 | The system SHALL recommend knowledge-transfer actions for high-risk person/service pairs. |
| F-REC-04 | All recommendations SHALL cite the evidence and risk score that motivated them. |
| F-REC-05 | Recommendations SHALL be prioritized by risk severity. |

### 3.7 Simulation Engine

| ID | Requirement |
|---|---|
| F-SIM-01 | The system SHALL support "what-if" removal simulations: "What happens if Person X leaves?" |
| F-SIM-02 | Simulations SHALL compute: affected systems, affected knowledge areas, alternative experts, risk delta. |
| F-SIM-03 | All simulation output SHALL be clearly labeled as SIMULATION / ESTIMATE. |
| F-SIM-04 | Simulations SHALL NOT be presented as predictions of employee behavior or intent. |

### 3.8 AI Assistant (RAG)

| ID | Requirement |
|---|---|
| F-RAG-01 | The system SHALL support natural-language queries about organizational knowledge. |
| F-RAG-02 | Answers SHALL be grounded: retrieved evidence must exist before answer generation. |
| F-RAG-03 | The assistant SHALL cite the source documents and graph evidence used in each answer. |
| F-RAG-04 | The assistant SHALL refuse to answer questions that cannot be supported by retrieved evidence. |
| F-RAG-05 | Retrieval SHALL combine vector search, graph search, and metadata filtering. |

### 3.9 Dashboard and Visualization

| ID | Requirement |
|---|---|
| F-UI-01 | The system SHALL provide an Executive Overview dashboard with summary risk metrics. |
| F-UI-02 | The system SHALL provide a Risk Explorer with filters by severity, team, project, system, knowledge area. |
| F-UI-03 | The system SHALL provide an interactive Knowledge Graph Explorer. |
| F-UI-04 | The system SHALL provide a Documentation Gap Dashboard. |
| F-UI-05 | The system SHALL provide individual Person Profile pages. |
| F-UI-06 | The system SHALL provide System Profile pages. |
| F-UI-07 | All risk displays SHALL show score, evidence, contributing factors, and confidence. |

### 3.10 Security and Access Control

| ID | Requirement |
|---|---|
| F-SEC-01 | The system SHALL require authentication for all API endpoints. |
| F-SEC-02 | The system SHALL enforce RBAC with three roles: Admin, Analyst, Viewer. |
| F-SEC-03 | The system SHALL isolate data by organization. |
| F-SEC-04 | The system SHALL support deletion of person data upon request (right-to-be-forgotten capability). |
| F-SEC-05 | The system SHALL maintain an audit log of all data access and mutation operations. |
| F-SEC-06 | The system SHALL validate and sanitize all user-provided inputs. |
| F-SEC-07 | No credentials or secrets SHALL be hardcoded. All secrets SHALL be environment-variable-based. |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement |
|---|---|
| NF-PERF-01 | Ingestion of a single document (≤ 100 pages) SHALL complete within 60 seconds. |
| NF-PERF-02 | Risk score queries SHALL respond within 2 seconds for datasets of ≤ 10,000 documents. |
| NF-PERF-03 | Vector similarity search SHALL respond within 1 second for up to 100,000 embeddings. |
| NF-PERF-04 | Graph traversal queries SHALL respond within 3 seconds for graphs of ≤ 100,000 nodes. |
| NF-PERF-05 | Dashboard page loads SHALL complete within 3 seconds. |

### 4.2 Reliability

| ID | Requirement |
|---|---|
| NF-REL-01 | Ingestion failures SHALL NOT corrupt existing data. |
| NF-REL-02 | The system SHALL be recoverable from a clean state using Docker Compose. |
| NF-REL-03 | All database migrations SHALL be idempotent and reversible. |

### 4.3 Reproducibility (Research)

| ID | Requirement |
|---|---|
| NF-REP-01 | The synthetic data generation SHALL be seeded and fully reproducible. |
| NF-REP-02 | Experiment configurations SHALL be stored with results. |
| NF-REP-03 | Model versions and configuration used in each experiment run SHALL be recorded. |
| NF-REP-04 | All evaluation metrics SHALL be computable from stored artifacts without re-running inference. |

### 4.4 Explainability

| ID | Requirement |
|---|---|
| NF-EXP-01 | Every risk score SHALL expose its calculation components and weights. |
| NF-EXP-02 | Every AI-generated claim SHALL trace back to at least one source document or graph edge. |
| NF-EXP-03 | Confidence scores SHALL be calibrated against validation labels where available. |

### 4.5 Ethical

| ID | Requirement |
|---|---|
| NF-ETH-01 | The system SHALL use synthetic identities for all development and testing. |
| NF-ETH-02 | Risk scores SHALL not be labeled or presented as employee performance metrics. |
| NF-ETH-03 | The system SHALL explicitly communicate the uncertainty and limitations of all risk assessments. |
| NF-ETH-04 | The system SHALL NOT support covert surveillance or tracking of individual employee behavior. |
| NF-ETH-05 | Documentation SHALL include explicit guidance on responsible use of risk scores. |

### 4.6 Maintainability

| ID | Requirement |
|---|---|
| NF-MNT-01 | All backend modules SHALL follow a consistent interface pattern. |
| NF-MNT-02 | All public functions SHALL have type annotations. |
| NF-MNT-03 | Test coverage for core intelligence modules SHALL be ≥ 80%. |
| NF-MNT-04 | Each major subsystem SHALL be independently testable. |

---

## 5. Constraints

- Backend: Python + FastAPI + PostgreSQL + Neo4j + pgvector
- Frontend: Next.js + React + TypeScript + Tailwind CSS
- Infrastructure: Docker + Docker Compose
- No cloud infrastructure required for MVP
- No external API calls to LLM providers during evaluation (to ensure reproducibility)
- The inference pipeline must NOT have access to synthetic data ground-truth labels during evaluation

---

## 6. Out of Scope for MVP

The following are explicitly deferred:

- Graph Neural Networks (GNN), Node2Vec, GraphSAGE
- Real-time streaming ingestion
- Multi-tenant SaaS infrastructure
- Mobile clients
- Integration with live GitHub/Jira APIs (MVP uses file exports)
- Advanced temporal GNNs

These may be addressed in post-MVP research extensions.

---

## 7. Dependencies Between Requirements

```
F-ING → F-EXT → F-KG → F-INT → F-RSK → F-REC
                              ↓
                           F-SIM
                              ↓
                           F-RAG → F-UI
```

Security (F-SEC) applies horizontally across all layers.

---

## 8. Acceptance Criteria for MVP

The MVP is accepted when the following end-to-end workflow succeeds with real (synthetic) data:

1. Upload a synthetic dataset (documents, code, issues, commits)
2. Parse all source types without errors
3. Extract entities and relationships with provenance
4. Generate and store embeddings
5. Construct knowledge graph in Neo4j
6. Compute expertise scores for all (Person, KnowledgeArea) pairs
7. Detect knowledge concentration and documentation gaps
8. Compute and explain risk scores
9. Show evidence for at least one CRITICAL risk
10. Generate at least three actionable recommendations
11. Display all of the above in the dashboard
