# MemoryLeak — Research Methodology

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Last Updated:** 2026-09-03

---

## 1. Research Problem

Organizations routinely lose critical knowledge when employees leave, change roles, or when documentation falls behind the systems it describes. This problem — organizational knowledge risk — is poorly quantified in practice. Existing approaches tend to be either purely manual (knowledge audits, exit interviews) or narrowly technical (code ownership metrics from git blame).

MemoryLeak investigates whether automated, hybrid AI systems can reliably detect and quantify organizational knowledge concentration and knowledge-loss risks at scale.

---

## 2. Central Research Question

> **RQ:** Can a hybrid system combining semantic embeddings, NLP entity extraction, knowledge graph analytics, and rule-based risk scoring reliably identify organizational knowledge concentration and knowledge-loss risks, and does the hybrid approach demonstrably outperform individual component-based baselines?

---

## 3. Research Sub-Questions

| ID | Sub-Question |
|---|---|
| RQ1 | How accurately can NLP and embedding-based methods extract person-knowledge-area expertise relationships from organizational documents? |
| RQ2 | How accurately can the system detect single-expert (bus-factor-1) knowledge areas compared to ground truth? |
| RQ3 | Does combining graph analytics with NLP-derived expertise scores improve risk detection compared to either method alone? |
| RQ4 | How does documentation staleness and coverage affect the accuracy of risk scores? |
| RQ5 | How faithful are AI-generated risk explanations to the underlying evidence? |

---

## 4. Hypotheses

| ID | Hypothesis | Falsifiable? |
|---|---|---|
| H1 | The hybrid system (embeddings + graph + rules) achieves higher F1 on bus-factor detection than any single baseline. | Yes — measured against ground-truth labels |
| H2 | Including temporal decay in expertise scoring reduces false negatives for stale experts. | Yes — ablation: hybrid vs hybrid without temporal features |
| H3 | Graph analytics contributes non-redundant signal over embedding-only expertise scoring. | Yes — ablation: hybrid vs hybrid minus graph features |
| H4 | Documentation coverage score negatively correlates with risk score error (i.e., more documentation → more accurate risk scores). | Yes — correlation analysis across synthetic scenarios |
| H5 | An LLM-only baseline (Phase 12 Baseline 3) produces higher false-positive rates due to hallucinated expertise claims. | Yes — measured against ground truth |

---

## 5. Experimental Design Overview

The research evaluation uses a four-baseline comparative design:

```
Baseline 1: Rule-Based System
    (git blame heuristics + keyword matching)
Baseline 2: Embedding-Based System
    (expertise scoring from semantic similarity only)
Baseline 3: LLM Classification
    (zero-shot risk classification by GPT-4-class model)
Baseline 4: Graph Analytics Only
    (centrality, degree, clustering from Neo4j — no NLP)

Proposed: Full Hybrid System
    (embeddings + NLP + graph + rules + temporal)
```

Followed by ablation:

```
Full Hybrid
Hybrid − Embeddings
Hybrid − Graph Features
Hybrid − Temporal Features
Hybrid − Documentation Features
```

Full details of experiments and evaluation scripts are in `docs/experiments.md`.

---

## 6. Evaluation Dataset

### 6.1 Synthetic Dataset Properties

The evaluation dataset is fully synthetic to:
1. Avoid privacy and consent issues with real employee data
2. Enable creation of known ground-truth labels
3. Ensure reproducibility

Target scale:
- 50+ people (employees)
- 10+ projects
- 20+ services (including critical, non-critical)
- 100+ knowledge areas
- 200+ documents
- 500+ issues
- 2,000+ commits
- 1,000+ discussions

### 6.2 Ground-Truth Labels

The synthetic data generator produces explicit ground-truth labels that the inference pipeline must not see:

| Label Type | Description |
|---|---|
| `bus_factor` | True bus factor value (integer) per service |
| `expert_ground_truth` | True (person, knowledge_area, score) triples |
| `stale_documents` | Boolean per document: truly stale or not |
| `undocumented_services` | Services with no meaningful documentation |
| `knowledge_silos` | Knowledge areas with concentration ≥ 0.9 |
| `doc_code_conflict` | Services where code and docs are meaningfully divergent |

### 6.3 Scenarios

The dataset includes deliberate test scenarios:

| Scenario | Description |
|---|---|
| S1: Single Expert | One person knows a critical knowledge area |
| S2: Multiple Experts | 3+ people have meaningful knowledge of an area |
| S3: Outdated Docs | Documents describing a service not updated in 18+ months |
| S4: Hidden Knowledge | Expert with deep knowledge but minimal documentation |
| S5: Fragmented Knowledge | No single person knows more than 30% of a system |
| S6: Doc/Code Conflict | Active code changes with no corresponding doc updates |
| S7: Critical Undocumented | High-criticality service with < 20% documentation coverage |
| S8: Employee Transition | Person historically active, now departing (no recent commits) |
| S9: Growing Concentration | Expert's share of commits increasing over time |
| S10: Healthy Distribution | Well-distributed knowledge, low risk |

These 10 scenarios must be represented across the test set.

---

## 7. Evaluation Metrics

### 7.1 Primary Task: Bus-Factor Detection

Binary classification: Does this service have bus_factor = 1? (positive class = at risk)

- Precision, Recall, F1 (macro and per-class)
- ROC-AUC
- False Positive Rate (false alarms)
- False Negative Rate (missed risks)

### 7.2 Knowledge-Area Expert Identification

Given a knowledge area, rank the people by expertise score and compare against ground truth.

- Precision@K (K = 1, 3, 5)
- NDCG@K
- Mean Reciprocal Rank

### 7.3 Documentation Coverage

Binary: Is this service documented sufficiently? (threshold-based against ground truth)

- Precision, Recall, F1

### 7.4 Explanation Faithfulness (Risk Explanations)

Qualitative and semi-quantitative:
- Evidence-Coverage Ratio: proportion of stated evidence items that are traceable to real source records
- Unsupported-Claim Rate: proportion of contributing factors that have no evidence record
- Evaluated on a random sample of 50 risk explanations

### 7.5 Retrieval Quality (RAG)

When applicable:
- Retrieval Recall@K: does the correct evidence appear in the top K retrieved chunks?
- Answer Groundedness: proportion of factual claims in the answer that are traceable to retrieved evidence

---

## 8. Evaluation Protocol

1. Generate synthetic dataset with ground-truth labels (Phase 2).
2. Store ground-truth labels in `data/evaluation/` — **sealed from the inference pipeline**.
3. Run each system (4 baselines + proposed + ablations) independently.
4. Each run is reproducible: fixed random seed, pinned model versions, logged configuration.
5. Evaluation scripts in `experiments/evaluation/` compute metrics from stored predictions.
6. Results stored in `experiments/results/` as JSON + CSV.
7. No manual adjustment of predictions after seeing ground truth.

### Fairness Constraints

- All systems use the same input data.
- No system has access to ground-truth labels during inference.
- LLM baseline (Baseline 3) uses a deterministic temperature=0 setting.
- Embedding model is identical across all systems that use embeddings.

---

## 9. Limitations of the Research Design

1. **Synthetic data generalization**: Findings on synthetic data may not fully transfer to real organizational environments with messier, more ambiguous signals.

2. **Ground-truth quality**: Ground-truth labels are generated by the same system that creates the data. They are internally consistent but not independently validated by human organizational experts.

3. **LLM provider dependency**: Baseline 3 (LLM classification) requires access to an LLM provider. The exact model and version must be pinned to ensure reproducibility. If the API is unavailable, this baseline cannot be reproduced without the same model weights.

4. **Single-domain synthetic data**: The synthetic data models a software engineering organization. Results may not generalize to other knowledge work domains (law, medicine, manufacturing).

5. **Embedding model choice**: Results are sensitive to the choice of embedding model. The primary evaluation uses `all-MiniLM-L6-v2`. A sensitivity analysis using a larger model is an optional extension.

6. **English-only**: The NLP pipeline is English-only. Multilingual organizations are explicitly out of scope.

---

## 10. Ethical Considerations

This research involves techniques that could, in theory, be used for invasive employee surveillance. The following safeguards apply:

- All development and evaluation uses fully synthetic identities. No real employee data is used.
- The system is designed to surface organizational knowledge gaps, not to evaluate individual employee performance.
- Risk scores must be accompanied by explicit uncertainty statements.
- The responsible-use documentation (see `docs/limitations.md`) must be consulted before deploying to a real organization.
- The system explicitly does not support: covert monitoring, alerting on individual behavior, ranking employees by productivity.

---

## 11. Related Work (Placeholder)

A formal literature review will be conducted before experimental evaluation begins. This section will be populated with:

- Prior work on organizational knowledge management systems
- Graph-based expertise finding systems
- NLP approaches for knowledge extraction from software artifacts
- Bus-factor and truck-factor metrics literature
- RAG and grounded QA systems

**IMPORTANT:** No research claims of novelty are made in this document until the literature review is complete.

---

## 12. Reproducibility Checklist

- [ ] Synthetic data generator seeded with fixed `RANDOM_SEED=42`
- [ ] All model versions pinned in `requirements.txt`
- [ ] Embedding model name and version stored per embedding record
- [ ] Experiment configurations stored alongside results
- [ ] Evaluation scripts are idempotent (re-running produces identical results)
- [ ] Docker image versions pinned in `docker-compose.yml`
- [ ] No manual result adjustments after ground-truth comparison
