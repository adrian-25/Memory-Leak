# MemoryLeak — Known Limitations and Ethical Constraints

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Last Updated:** 2026-09-03

---

## 1. Purpose of This Document

This document records known technical limitations, research scope boundaries, and ethical constraints. It exists to:

1. Communicate honestly what the system can and cannot do.
2. Prevent misuse of risk scores.
3. Set appropriate expectations for evaluators and users.
4. Serve as a permanent record of acknowledged limitations (not cleared without evidence).

This document is updated as new limitations are discovered. Limitations are never removed unless the underlying issue has been resolved with documented evidence.

---

## 2. Technical Limitations

### LIM-TECH-01: Synthetic Data Only (MVP)

**Status:** Current limitation
**Affects:** All phases

The MVP uses exclusively synthetic organizational data. Risk scores and system behavior have not been validated against real organizational datasets. Generalization to real-world environments is unproven.

**Mitigation:** The synthetic data is designed to reflect plausible organizational structures and knowledge distributions. A real-data validation study is a post-MVP research extension.

---

### LIM-TECH-02: English Language Only

**Status:** Current limitation
**Affects:** NLP pipeline, entity extraction, embeddings

The spaCy NER pipeline is trained on English corpora. The embedding model (`all-MiniLM-L6-v2`) has limited multilingual capability. Performance on non-English documents is not characterized.

**Mitigation:** The `SPACY_MODEL` and `EMBEDDING_MODEL` environment variables allow model swapping. Multilingual models (e.g., `paraphrase-multilingual-MiniLM-L12-v2`) can be substituted, but performance is not evaluated.

---

### LIM-TECH-03: File Export Ingestion Only (MVP)

**Status:** Current limitation
**Affects:** Ingestion pipeline

The MVP ingests static file exports (JSON, PDF, DOCX, etc.). It does not connect to live APIs (GitHub, Jira, Confluence, Slack). Knowledge is therefore a point-in-time snapshot, not continuously updated.

**Mitigation:** The ingestion architecture is designed to accommodate additional source types. Live API connectors are a Phase post-MVP extension.

---

### LIM-TECH-04: Approximate Nearest Neighbor Search

**Status:** Permanent limitation (by design)
**Affects:** Vector similarity search

pgvector's IVFFlat index uses approximate nearest neighbor search. For small datasets (< 50,000 chunks), exact search is used. For larger datasets, a small number of truly relevant chunks may not be retrieved.

**Mitigation:** IVFFlat `lists` parameter is tuned to dataset size. Retrieval recall is evaluated as part of the RAG quality metrics (EXP-S1 et al.).

---

### LIM-TECH-05: Knowledge Graph is a Derived View

**Status:** Permanent architectural characteristic
**Affects:** Knowledge graph consistency

Neo4j is populated by the ingestion pipeline from PostgreSQL data. The graph is not the system of record. If PostgreSQL data is deleted, the graph must be re-derived. If the graph and PostgreSQL diverge, the correct version is PostgreSQL.

**Mitigation:** A graph-rebuild script is provided. Incremental sync is implemented as part of the ingestion pipeline.

---

### LIM-TECH-06: Expertise Scores Are Evidence-Based Proxies

**Status:** Permanent limitation
**Affects:** Expertise scoring, all downstream risk scores

Expertise scores are computed from observable evidence (commits, documents, issues). They do not directly measure cognitive knowledge. A person may have deep expertise that left no written record (e.g., knowledge acquired verbally, undocumented institutional memory).

**Mitigation:** The system explicitly labels all expertise scores with confidence values. Risk scores derived from low-evidence expertise scores carry lower confidence.

---

### LIM-TECH-07: No Real-Time Risk Updates

**Status:** Current limitation
**Affects:** Dashboard, risk scores

Risk scores are pre-computed on a scheduled basis, not in real time. The `risk_scores.computed_at` field indicates when the score was last updated. Scores may be stale if new ingestion has not triggered a re-computation.

**Mitigation:** The dashboard displays `computed_at` prominently. A manual "re-compute" trigger is available to Analysts and Admins.

---

### LIM-TECH-08: Token Revocation Not Implemented in MVP

**Status:** Current limitation
**Affects:** Security, authentication

JWT access tokens (15-minute TTL) cannot be individually revoked in the MVP. If a token is compromised, it remains valid until expiry. Refresh tokens (7-day TTL) are not stored server-side in MVP.

**Mitigation:** Short access token TTL (15 min) limits the impact window. Full token revocation via blocklist is a Phase 1 enhancement candidate.

---

### LIM-TECH-09: LLM Baseline Non-Determinism

**Status:** Research limitation
**Affects:** EXP-B3 (LLM Classification Baseline)

Even at temperature=0, LLM API outputs may differ across API versions, dates, and model updates. The LLM Baseline experiment result is tied to a specific model version. Future reproduction may yield different results.

**Mitigation:** The API call log for EXP-B3 records the model version, request timestamps, and complete prompts/responses.

---

### LIM-TECH-10: Risk Score Weights Are Not Empirically Calibrated in MVP

**Status:** Current limitation
**Affects:** Risk aggregation

The risk aggregation weights (e.g., `commit_frequency: 0.30, authorship: 0.25`) are initially set based on domain reasoning, not from empirical calibration on real-world data. They will be explored in the sensitivity analysis (EXP-S3).

**Mitigation:** Weights are fully configurable. Sensitivity analysis measures the effect of weight variation.

---

## 3. Research Limitations

### LIM-RES-01: Single-Domain Evaluation

The evaluation dataset models a software engineering organization. Claims of system performance are limited to this domain. Knowledge work in legal, medical, manufacturing, or other domains may have fundamentally different knowledge signal patterns.

---

### LIM-RES-02: Ground Truth is Synthetic

Ground-truth labels are generated by the same synthetic data generator that produces the dataset. They are internally consistent but not validated by independent human organizational experts. This limits the external validity of the quantitative results.

---

### LIM-RES-03: No Literature Review at Phase 0

A formal literature review has not yet been conducted. No claims of novelty or superiority over existing approaches are made until the review is complete (to be done before Phase 12).

---

### LIM-RES-04: Single Random Seed

The primary evaluation uses `RANDOM_SEED=42`. It is possible that results are sensitive to the specific random realization of the synthetic data. A multi-seed sensitivity analysis is an optional extension.

---

## 4. Ethical Constraints and Responsible Use

### 4.1 What This System Is

MemoryLeak is designed to identify organizational knowledge concentration risks — gaps and dependencies in the organization's collective knowledge — to support proactive knowledge management.

### 4.2 What This System Is Not

- **Not a performance evaluation tool.** Risk scores must not be used to evaluate employee performance, set compensation, or make employment decisions.
- **Not a surveillance tool.** The system surfaces organizational patterns, not individual behavioral monitoring.
- **Not a prediction of employee intent.** Simulation outputs are organizational risk estimates, not predictions of whether a person will leave.

### 4.3 Prohibited Uses

The following uses of MemoryLeak are explicitly against its design intent and must be prevented by organizational policy:

- Using expertise scores as a basis for promotion, demotion, or termination decisions
- Using departure simulations as evidence of individual employees being "flight risks"
- Treating the absence of written evidence as proof of lack of knowledge
- Presenting risk scores to employees as performance feedback without their knowledge
- Deploying the system for covert monitoring of employee activity

### 4.4 Required Disclosures

Any organization deploying MemoryLeak should:
1. Inform employees that their activity data is being analyzed for organizational knowledge health purposes.
2. Establish a clear policy on how risk scores will and will not be used.
3. Provide employees access to their own knowledge profiles.
4. Allow employees to submit corrections to their profiles.

### 4.5 Uncertainty Communication

Every risk score is accompanied by:
- A confidence value (0.0–1.0)
- A `limitations` text field explaining what the score does NOT capture
- A `computed_at` timestamp

The dashboard must display confidence prominently alongside all scores.

---

## 5. Open Questions (Phase 0)

The following questions are unresolved at Phase 0 and will be addressed in later phases:

| ID | Question | Target Phase |
|---|---|---|
| OQ-01 | What is the minimum evidence threshold below which a risk score is unreliable? | Phase 6 |
| OQ-02 | How do we handle entities with the same name (person name collisions)? | Phase 2/3 |
| OQ-03 | How should implicit knowledge (inferred from code style/patterns) be weighted vs. explicit (docs)? | Phase 4 |
| OQ-04 | How do we handle team restructuring events in the knowledge graph? | Phase 5 |
| OQ-05 | What is the optimal chunking strategy for code vs. prose documents? | Phase 3/4 |
