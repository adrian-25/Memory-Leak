# MemoryLeak — Experiments Plan

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Last Updated:** 2026-09-03

---

## 1. Overview

This document defines all planned experiments for the MemoryLeak research evaluation. Experiments are not executed until the full MVP pipeline is operational (Phases 1–11). Each experiment has a defined:

- Purpose
- Input data
- Method configuration
- Metrics collected
- Expected output artifacts
- Status

> **CRITICAL:** No results are reported in this document. Results will be populated in `experiments/results/` during Phase 12. All result values in this document are targets and thresholds, not actual measurements. Do not fabricate results.

---

## 2. Experiment Status Definitions

| Status | Meaning |
|---|---|
| PLANNED | Designed, not yet implemented |
| IMPLEMENTED | Script exists but not yet run |
| RUNNING | Currently executing |
| COMPLETED | Executed and results stored |
| BLOCKED | Depends on unfinished component |

---

## 3. Evaluation Dataset

All experiments use the same dataset:

**Dataset:** `data/synthetic/v1/` (generated in Phase 2)
**Ground Truth:** `data/evaluation/ground_truth_v1.json` (sealed from inference)
**Random Seed:** 42
**Dataset Version:** 1.0

### Dataset Composition

| Entity | Count |
|---|---|
| People | 52 |
| Teams | 8 |
| Projects | 12 |
| Services | 24 |
| Knowledge Areas | 108 |
| Documents | 247 |
| Commits | 2,148 |
| Issues | 512 |
| Discussions | 1,034 |
| Scenarios covered | S1–S10 (all) |

---

## 4. Baseline Systems

### EXP-B1: Rule-Based Baseline

**Status:** PLANNED
**Phase:** 12

**Description:**
A simple rule-based system that detects knowledge concentration using heuristics derived from raw metadata.

**Method:**
- Bus factor: count distinct commit authors per service in the last 90 days. If count = 1, bus_factor_1 = True.
- Expertise score: `commits_by_person / total_commits` for each (person, service) pair.
- Documentation coverage: `document_count / expected_documents` using a fixed mapping.
- Staleness: document not updated in 180+ days = stale.
- No NLP, no embeddings, no graph analysis.

**Configuration:**
```yaml
name: rule_based_baseline
commit_window_days: 90
staleness_threshold_days: 180
min_doc_coverage_ratio: 0.5
```

**Output artifacts:**
- `experiments/results/baseline_rule/predictions.json`
- `experiments/results/baseline_rule/metrics.json`

---

### EXP-B2: Embedding-Only Baseline

**Status:** PLANNED
**Phase:** 12

**Description:**
Uses only semantic embeddings to identify expertise relationships. No graph traversal, no rule-based scoring.

**Method:**
- Embed all document chunks.
- For each (person, knowledge_area) pair, compute expertise as the average cosine similarity between: (a) the person's authored chunks, (b) the knowledge area's name embedding.
- Bus factor: count persons with expertise score > 0.5 per service.
- Documentation coverage: ratio of document embeddings in a service's knowledge area cluster.
- No temporal weighting.

**Configuration:**
```yaml
name: embedding_baseline
model: all-MiniLM-L6-v2
expertise_threshold: 0.5
similarity_metric: cosine
```

**Output artifacts:**
- `experiments/results/baseline_embedding/predictions.json`
- `experiments/results/baseline_embedding/metrics.json`

---

### EXP-B3: LLM Classification Baseline

**Status:** PLANNED
**Phase:** 12

**Prerequisites:** Access to LLM API (model to be determined)

**Description:**
Uses zero-shot LLM classification to assign expertise and risk scores. Represents the naive "just ask the LLM" approach.

**Method:**
- For each (person, knowledge_area) pair, provide the LLM with the person's document excerpts and commit messages, and ask it to classify expertise on a 0–1 scale.
- For each service, provide summarized activity and ask for a bus-factor estimate.
- Temperature = 0 (deterministic).

**Configuration:**
```yaml
name: llm_baseline
model: gpt-4o-mini  # or equivalent, to be confirmed
temperature: 0
max_tokens: 512
```

**Limitations:**
- Non-determinism cannot be fully eliminated even at temperature=0 across API versions.
- Cost constrains the number of (person, knowledge_area) pairs that can be evaluated.
- If LLM API is unavailable, this baseline is BLOCKED.

**Output artifacts:**
- `experiments/results/baseline_llm/predictions.json`
- `experiments/results/baseline_llm/metrics.json`
- `experiments/results/baseline_llm/api_call_log.json`

---

### EXP-B4: Graph Analytics Baseline

**Status:** PLANNED
**Phase:** 12

**Description:**
Uses graph structural properties exclusively. No NLP, no embeddings.

**Method:**
- Build the knowledge graph from commit and authorship metadata only (no document content analysis).
- Compute node degree centrality for Person nodes per KnowledgeArea subgraph.
- Bus factor: degree centrality of the top person > 0.9 in a service's CONTRIBUTED_TO neighborhood.
- Expertise score: normalized betweenness centrality.
- Documentation coverage: ratio of KnowledgeArea nodes with DESCRIBED_BY edges to Document nodes.

**Configuration:**
```yaml
name: graph_analytics_baseline
centrality_algorithm: betweenness
normalization: min_max
```

**Output artifacts:**
- `experiments/results/baseline_graph/predictions.json`
- `experiments/results/baseline_graph/metrics.json`

---

## 5. Proposed System

### EXP-P1: Full Hybrid System

**Status:** PLANNED
**Phase:** 12

**Description:**
The complete MemoryLeak pipeline: NLP entity extraction + semantic embeddings + graph analytics + temporal decay + rule-based risk aggregation.

**Method:**
Full pipeline as documented in `docs/architecture.md`, Section 3.1 and 3.2.

Components active:
- spaCy NER + EntityRuler patterns
- sentence-transformers embeddings (all-MiniLM-L6-v2)
- Neo4j knowledge graph traversal
- Temporal decay (λ = 0.005, configurable)
- Risk aggregator with weighted scoring

**Configuration:**
```yaml
name: hybrid_proposed
nlp_model: en_core_web_sm
embedding_model: all-MiniLM-L6-v2
temporal_decay_lambda: 0.005
expertise_threshold: 0.5
risk_weights:
  commit_frequency: 0.30
  authorship: 0.25
  issue_resolution: 0.20
  doc_authorship: 0.15
  discussion_depth: 0.10
```

**Output artifacts:**
- `experiments/results/proposed_hybrid/predictions.json`
- `experiments/results/proposed_hybrid/metrics.json`
- `experiments/results/proposed_hybrid/explanations_sample.json`

---

## 6. Ablation Studies

### EXP-A1: Hybrid Without Embeddings

**Status:** PLANNED
**Phase:** 13

**Method:** Full hybrid pipeline with embedding similarity score set to 0 (embeddings not used for expertise scoring). Graph and rule components unchanged.

**Purpose:** Isolate the contribution of semantic embeddings.

---

### EXP-A2: Hybrid Without Graph Features

**Status:** PLANNED
**Phase:** 13

**Method:** Full hybrid pipeline without Neo4j traversal. Graph-derived features (dependency chains, centrality) replaced with direct SQL aggregates.

**Purpose:** Isolate the contribution of graph analytics.

---

### EXP-A3: Hybrid Without Temporal Features

**Status:** PLANNED
**Phase:** 13

**Method:** Full hybrid pipeline with temporal decay λ set to 0 (no recency weighting).

**Purpose:** Measure the value of temporal decay.

---

### EXP-A4: Hybrid Without Documentation Features

**Status:** PLANNED
**Phase:** 13

**Method:** Full hybrid pipeline excluding documentation coverage and staleness scores from the risk aggregator.

**Purpose:** Measure the contribution of documentation signals.

---

## 7. Sensitivity Analyses

### EXP-S1: Embedding Model Sensitivity

**Status:** PLANNED
**Phase:** Post-evaluation (optional extension)

**Method:** Re-run proposed hybrid with a larger embedding model (`all-mpnet-base-v2`, 768 dimensions) and compare F1.

**Purpose:** Assess sensitivity to embedding model choice.

---

### EXP-S2: Temporal Decay Parameter Sensitivity

**Status:** PLANNED
**Phase:** Post-evaluation (optional extension)

**Method:** Grid search over λ ∈ {0.001, 0.003, 0.005, 0.010, 0.020}. Measure F1 on bus-factor detection.

**Purpose:** Find optimal decay rate and characterize sensitivity.

---

### EXP-S3: Risk Weight Sensitivity

**Status:** PLANNED
**Phase:** Post-evaluation (optional extension)

**Method:** Vary risk aggregation weights (commit_frequency, authorship, etc.) across a defined grid. Measure F1 on bus-factor detection.

**Purpose:** Understand sensitivity to weighting scheme.

---

## 8. Evaluation Scripts

All evaluation scripts are in `experiments/evaluation/`. Each script:

- Takes predictions JSON + ground truth JSON as input
- Produces a metrics JSON file
- Is idempotent (re-running produces the same result)
- Does not modify ground-truth files

| Script | Purpose |
|---|---|
| `compute_bus_factor_metrics.py` | Precision, Recall, F1, ROC-AUC for bus-factor detection |
| `compute_expertise_ranking.py` | Precision@K, NDCG@K, MRR for expertise ranking |
| `compute_doc_coverage_metrics.py` | Precision, Recall, F1 for documentation coverage |
| `compute_explanation_faithfulness.py` | Evidence-coverage ratio, unsupported-claim rate |
| `compute_retrieval_quality.py` | Retrieval Recall@K, answer groundedness |
| `generate_comparison_table.py` | Aggregates all results into comparison table |

---

## 9. Results Reporting Requirements

When results are available (Phase 12+), they MUST be reported as follows:

1. Raw metric values to 4 decimal places.
2. No rounding that would change ordering.
3. Confidence intervals where possible (bootstrap resampling, n=1000).
4. System configuration version logged alongside results.
5. If a baseline is unavailable (e.g., LLM API), mark it as `NOT_RUN` with reason.
6. No selective reporting: if a metric is defined, it must be reported for all systems.

### Prohibited Practices

- Reporting only the metrics where the proposed system wins.
- Adjusting the proposed system configuration after seeing ground-truth comparison.
- Reporting approximate or rounded values that make differences appear larger than they are.
- Claiming results before experiments are run.

---

## 10. Experiment Log

Results will be recorded here as experiments are completed. This section is empty until Phase 12.

| Experiment | Status | Date Run | Results Location |
|---|---|---|---|
| EXP-B1 Rule-Based | PLANNED | — | — |
| EXP-B2 Embedding-Only | PLANNED | — | — |
| EXP-B3 LLM Baseline | PLANNED | — | — |
| EXP-B4 Graph Analytics | PLANNED | — | — |
| EXP-P1 Full Hybrid | PLANNED | — | — |
| EXP-A1 No Embeddings | PLANNED | — | — |
| EXP-A2 No Graph | PLANNED | — | — |
| EXP-A3 No Temporal | PLANNED | — | — |
| EXP-A4 No Docs | PLANNED | — | — |
