# MemoryLeak — Data Model

**Version:** 0.1.0
**Status:** Phase 0 — Planning
**Last Updated:** 2026-09-03

---

## 1. Overview

MemoryLeak uses three complementary storage systems:

| Store | Purpose | Technology |
|---|---|---|
| Relational Database | Documents, chunks, metadata, risk scores, users, audit logs | PostgreSQL 16 |
| Vector Store | Chunk embeddings for semantic search | pgvector (PostgreSQL extension) |
| Graph Database | Entities, relationships, knowledge graph | Neo4j 5.x |

The stores are complementary, not redundant. PostgreSQL holds the canonical source of truth for all records. Neo4j holds the traversable knowledge graph. pgvector enables semantic search over document chunks.

---

## 2. Relational Schema (PostgreSQL)

### 2.1 Naming Conventions

- Tables: `snake_case`, plural
- Primary keys: `id UUID DEFAULT gen_random_uuid()`
- Foreign keys: `{table_singular}_id`
- Timestamps: `created_at`, `updated_at` on all mutable tables
- Soft deletes: `deleted_at TIMESTAMPTZ NULL` on sensitive tables

---

### 2.2 Core Tables

#### `organizations`

```sql
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
```

#### `users`

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email           TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'analyst', 'viewer')),
    password_hash   TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    UNIQUE (organization_id, email)
);
```

---

### 2.3 Ingestion Tables

#### `raw_sources`

Tracks every uploaded source file or data feed.

```sql
CREATE TABLE raw_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    source_type     TEXT NOT NULL CHECK (source_type IN (
                        'pdf', 'docx', 'markdown', 'txt',
                        'python', 'javascript', 'typescript',
                        'java', 'sql', 'yaml', 'json', 'toml', 'ini',
                        'issues', 'commits', 'discussions'
                    )),
    file_name       TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    content_hash    TEXT NOT NULL,     -- SHA-256 of raw content
    file_size_bytes BIGINT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN (
                        'pending', 'processing', 'completed', 'failed'
                    )),
    error_message   TEXT,
    ingested_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_raw_sources_org ON raw_sources(organization_id);
CREATE INDEX idx_raw_sources_status ON raw_sources(status);
CREATE UNIQUE INDEX idx_raw_sources_hash_org ON raw_sources(organization_id, content_hash);
```

#### `documents`

Parsed and normalized documents.

```sql
CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    raw_source_id   UUID NOT NULL REFERENCES raw_sources(id),
    title           TEXT,
    document_type   TEXT NOT NULL,     -- mirrors source_type
    author_name     TEXT,              -- extracted or provided
    author_id       UUID,              -- references people.id if resolved
    authored_at     TIMESTAMPTZ,       -- from metadata or filename
    last_modified   TIMESTAMPTZ,
    language        TEXT,              -- detected language
    word_count      INT,
    content_hash    TEXT NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_org ON documents(organization_id);
CREATE INDEX idx_documents_author ON documents(author_id);
CREATE INDEX idx_documents_type ON documents(document_type);
```

#### `document_chunks`

Chunked segments of parsed documents.

```sql
CREATE TABLE document_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    chunk_index     INT NOT NULL,
    content         TEXT NOT NULL,
    token_count     INT,
    start_char      INT,               -- character offset in parent document
    end_char        INT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_org ON document_chunks(organization_id);
```

#### `chunk_embeddings`

Vector embeddings for semantic search (pgvector).

```sql
CREATE TABLE chunk_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id        UUID NOT NULL UNIQUE REFERENCES document_chunks(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    model_name      TEXT NOT NULL,     -- e.g. "all-MiniLM-L6-v2"
    model_version   TEXT NOT NULL,
    embedding       VECTOR(384),       -- dimension matches model
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_embeddings_org ON chunk_embeddings(organization_id);
-- IVFFlat index for approximate nearest neighbor (created after bulk load)
-- CREATE INDEX idx_embeddings_vector ON chunk_embeddings
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

### 2.4 Domain Entity Tables

#### `people`

Synthetic people (employees) extracted or provided.

```sql
CREATE TABLE people (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    display_name    TEXT NOT NULL,
    synthetic_id    TEXT UNIQUE NOT NULL,  -- stable identifier from data gen
    email_hash      TEXT,                  -- hashed, not stored in plain text
    team_id         UUID,
    role_title      TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_people_org ON people(organization_id);
CREATE INDEX idx_people_team ON people(team_id);
```

#### `teams`

```sql
CREATE TABLE teams (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name            TEXT NOT NULL,
    parent_team_id  UUID REFERENCES teams(id),
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `projects`

```sql
CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name            TEXT NOT NULL,
    description     TEXT,
    status          TEXT CHECK (status IN ('active', 'inactive', 'archived')),
    team_id         UUID REFERENCES teams(id),
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `services`

```sql
CREATE TABLE services (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organizations(id),
    name                TEXT NOT NULL,
    description         TEXT,
    criticality         TEXT CHECK (criticality IN ('critical', 'high', 'medium', 'low')),
    project_id          UUID REFERENCES projects(id),
    primary_owner_id    UUID REFERENCES people(id),
    repository_url      TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `knowledge_areas`

```sql
CREATE TABLE knowledge_areas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name            TEXT NOT NULL,
    description     TEXT,
    category        TEXT,              -- e.g. "technology", "domain", "process"
    parent_area_id  UUID REFERENCES knowledge_areas(id),
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 2.5 Event / Activity Tables

#### `commits`

```sql
CREATE TABLE commits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    external_id     TEXT NOT NULL,     -- original commit hash
    author_id       UUID REFERENCES people(id),
    service_id      UUID REFERENCES services(id),
    message         TEXT,
    files_changed   JSONB DEFAULT '[]',
    additions       INT,
    deletions       INT,
    committed_at    TIMESTAMPTZ NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_commits_author ON commits(author_id);
CREATE INDEX idx_commits_service ON commits(service_id);
CREATE INDEX idx_commits_date ON commits(committed_at DESC);
```

#### `issues`

```sql
CREATE TABLE issues (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    external_id     TEXT NOT NULL,
    title           TEXT NOT NULL,
    body            TEXT,
    status          TEXT,
    author_id       UUID REFERENCES people(id),
    assignee_id     UUID REFERENCES people(id),
    resolver_id     UUID REFERENCES people(id),
    service_id      UUID REFERENCES services(id),
    project_id      UUID REFERENCES projects(id),
    created_at_ext  TIMESTAMPTZ,
    closed_at_ext   TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `discussions`

```sql
CREATE TABLE discussions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    external_id     TEXT NOT NULL,
    thread_id       TEXT,
    author_id       UUID REFERENCES people(id),
    content         TEXT,
    parent_id       UUID REFERENCES discussions(id),
    created_at_ext  TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 2.6 Intelligence / Scoring Tables

#### `expertise_scores`

```sql
CREATE TABLE expertise_scores (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organizations(id),
    person_id           UUID NOT NULL REFERENCES people(id),
    knowledge_area_id   UUID NOT NULL REFERENCES knowledge_areas(id),
    score               NUMERIC(5, 4) NOT NULL CHECK (score BETWEEN 0 AND 1),
    recency_score       NUMERIC(5, 4),
    breadth_score       NUMERIC(5, 4),
    depth_score         NUMERIC(5, 4),
    confidence          NUMERIC(5, 4) NOT NULL,
    evidence_count      INT NOT NULL DEFAULT 0,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (person_id, knowledge_area_id)
);

CREATE INDEX idx_expertise_person ON expertise_scores(person_id);
CREATE INDEX idx_expertise_area ON expertise_scores(knowledge_area_id);
```

#### `risk_scores`

```sql
CREATE TABLE risk_scores (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organizations(id),
    entity_type         TEXT NOT NULL CHECK (entity_type IN (
                            'person', 'service', 'project',
                            'knowledge_area', 'organization'
                        )),
    entity_id           UUID NOT NULL,
    risk_category       TEXT NOT NULL CHECK (risk_category IN (
                            'bus_factor', 'knowledge_concentration',
                            'documentation_coverage', 'documentation_staleness',
                            'doc_code_drift', 'dependency_risk', 'overall'
                        )),
    score               NUMERIC(5, 4) NOT NULL CHECK (score BETWEEN 0 AND 1),
    severity            TEXT NOT NULL CHECK (severity IN (
                            'critical', 'high', 'medium', 'low', 'info'
                        )),
    confidence          NUMERIC(5, 4) NOT NULL,
    contributing_factors JSONB NOT NULL DEFAULT '[]',
    limitations         TEXT,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (entity_type, entity_id, risk_category)
);

CREATE INDEX idx_risk_entity ON risk_scores(entity_type, entity_id);
CREATE INDEX idx_risk_severity ON risk_scores(severity);
CREATE INDEX idx_risk_category ON risk_scores(risk_category);
```

#### `evidence_records`

Provenance for every AI-generated claim or risk score.

```sql
CREATE TABLE evidence_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    claim_type      TEXT NOT NULL,         -- "expertise", "risk", "relationship"
    claim_id        UUID NOT NULL,         -- FK to the relevant score/claim table
    source_type     TEXT NOT NULL,         -- "document", "commit", "issue", "graph_edge"
    source_id       UUID NOT NULL,
    chunk_id        UUID REFERENCES document_chunks(id),
    span_start      INT,
    span_end        INT,
    excerpt         TEXT,
    inference_type  TEXT NOT NULL,         -- "direct", "inferred", "aggregated"
    confidence      NUMERIC(5, 4) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evidence_claim ON evidence_records(claim_type, claim_id);
CREATE INDEX idx_evidence_source ON evidence_records(source_type, source_id);
```

#### `recommendations`

```sql
CREATE TABLE recommendations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organizations(id),
    recommendation_type TEXT NOT NULL CHECK (recommendation_type IN (
                            'document_gap', 'backup_expert',
                            'knowledge_transfer', 'risk_mitigation'
                        )),
    priority            TEXT NOT NULL CHECK (priority IN (
                            'critical', 'high', 'medium', 'low'
                        )),
    title               TEXT NOT NULL,
    description         TEXT NOT NULL,
    target_entity_type  TEXT,
    target_entity_id    UUID,
    risk_score_id       UUID REFERENCES risk_scores(id),
    evidence_ids        UUID[] DEFAULT '{}',
    status              TEXT NOT NULL DEFAULT 'open' CHECK (status IN (
                            'open', 'in_progress', 'resolved', 'dismissed'
                        )),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 2.7 Audit and Security Tables

#### `audit_logs`

```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id         UUID REFERENCES users(id),
    operation       TEXT NOT NULL,         -- "create", "read", "update", "delete", "export"
    entity_type     TEXT NOT NULL,
    entity_id       UUID,
    ip_address      INET,
    user_agent      TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_time ON audit_logs(created_at DESC);
```

---

## 3. Graph Model (Neo4j)

### 3.1 Node Labels and Properties

```
(:Person)
    Properties:
    - id: string (UUID, matches people.id)
    - organization_id: string
    - display_name: string
    - synthetic_id: string
    - is_active: boolean

(:Team)
    Properties:
    - id: string
    - organization_id: string
    - name: string

(:Project)
    Properties:
    - id: string
    - organization_id: string
    - name: string
    - status: string

(:Service)
    Properties:
    - id: string
    - organization_id: string
    - name: string
    - criticality: string

(:Document)
    Properties:
    - id: string
    - organization_id: string
    - title: string
    - document_type: string
    - authored_at: datetime
    - last_modified: datetime

(:KnowledgeArea)
    Properties:
    - id: string
    - organization_id: string
    - name: string
    - category: string

(:Technology)
    Properties:
    - id: string
    - organization_id: string
    - name: string
    - version: string

(:CodeComponent)
    Properties:
    - id: string
    - organization_id: string
    - name: string
    - component_type: string    -- "module", "class", "function", "file"
    - service_id: string
```

### 3.2 Relationship Types and Properties

```
(:Person)-[:KNOWS {
    score: float,            -- expertise score 0-1
    confidence: float,
    evidence_count: int,
    last_evidenced_at: datetime
}]->(:KnowledgeArea)

(:Person)-[:AUTHORED {
    contribution_type: string,  -- "primary", "secondary"
    authored_at: datetime,
    confidence: float
}]->(:Document)

(:Person)-[:CONTRIBUTED_TO {
    commit_count: int,
    first_commit_at: datetime,
    last_commit_at: datetime,
    additions: int,
    deletions: int
}]->(:Service)

(:Person)-[:CONTRIBUTED_TO]->(: Repository)

(:Person)-[:RESOLVED {
    resolution_time_hours: float,
    confidence: float
}]->(:Issue)

(:Person)-[:OWNS {
    ownership_type: string,    -- "primary", "secondary"
    since: datetime
}]->(:Service)

(:Person)-[:MEMBER_OF {
    since: datetime
}]->(:Team)

(:Team)-[:WORKS_ON]->(:Project)

(:Project)-[:DEPENDS_ON {
    dependency_type: string,   -- "hard", "soft", "optional"
    confidence: float
}]->(:Service)

(:Service)-[:IMPLEMENTED_BY]->(:CodeComponent)

(:Service)-[:DEPENDS_ON {
    dependency_type: string
}]->(:Service)

(:Document)-[:DESCRIBES {
    coverage_score: float,
    confidence: float
}]->(:Service)

(:Document)-[:DESCRIBES]->(:KnowledgeArea)

(:CodeComponent)-[:USES]->(:Technology)

(:KnowledgeArea)-[:PARENT_OF]->(:KnowledgeArea)
```

### 3.3 Key Cypher Queries

**Bus-factor analysis for a service:**
```cypher
MATCH (s:Service {id: $service_id})
MATCH (p:Person)-[:CONTRIBUTED_TO]->(s)
WITH s, count(p) AS contributor_count, collect(p) AS contributors
RETURN s.name, contributor_count, contributors
ORDER BY contributor_count ASC
```

**Knowledge dependency chain:**
```cypher
MATCH (p:Person {id: $person_id})-[:KNOWS]->(ka:KnowledgeArea)
MATCH (s:Service)-[:DESCRIBED_BY]->(d:Document)-[:DESCRIBES]->(ka)
RETURN p.display_name, ka.name, collect(s.name) AS dependent_services
```

**Identify knowledge silos:**
```cypher
MATCH (ka:KnowledgeArea)
MATCH (p:Person)-[r:KNOWS]->(ka)
WITH ka, count(p) AS expert_count, max(r.score) AS max_score
WHERE expert_count <= 1
RETURN ka.name, expert_count, max_score
ORDER BY max_score DESC
```

**What-if simulation — person departure:**
```cypher
MATCH (p:Person {id: $person_id})-[:KNOWS]->(ka:KnowledgeArea)
MATCH (s:Service)-[:DEPENDS_ON_KA]->(ka)
WHERE NOT EXISTS {
    MATCH (other:Person)-[:KNOWS]->(ka)
    WHERE other.id <> $person_id AND other.is_active = true
}
RETURN s.name AS orphaned_service, ka.name AS orphaned_knowledge_area
```

---

## 4. Vector Model (pgvector)

### 4.1 Embedding Strategy

- Model: `all-MiniLM-L6-v2` (384 dimensions) — default for MVP
- Chunking: 512 tokens with 64-token overlap (documents); per-function for code
- Stored in: `chunk_embeddings.embedding VECTOR(384)`
- Similarity metric: cosine similarity

### 4.2 Retrieval Strategy

```sql
-- Top-K semantic search for a query embedding
SELECT
    ce.chunk_id,
    dc.content,
    d.title,
    d.document_type,
    1 - (ce.embedding <=> $query_embedding::vector) AS similarity
FROM chunk_embeddings ce
JOIN document_chunks dc ON dc.id = ce.chunk_id
JOIN documents d ON d.id = dc.document_id
WHERE ce.organization_id = $org_id
ORDER BY ce.embedding <=> $query_embedding::vector
LIMIT 20;
```

### 4.3 Index Strategy

- Use IVFFlat index for approximate nearest neighbor search
- Lists parameter: `sqrt(row_count)` rounded to nearest 100
- Created after bulk data load, not during ingestion

---

## 5. Entity Resolution Strategy

The same real-world entity may appear in multiple sources with slightly different names (e.g., "Alice Smith", "asmith", "A. Smith"). The system resolves these using:

1. Exact match on synthetic_id (for generated data)
2. Fuzzy name matching (for ingested real data)
3. Email hash matching
4. Manual override API

All resolution decisions are stored with confidence and can be reviewed.

---

## 6. Temporal Data Strategy

All records that carry time-sensitive meaning include:

- `authored_at` / `committed_at` / `created_at_ext` — original event time
- `last_modified` — for staleness calculation
- `computed_at` — when the score or inference was generated

Staleness score calculation:

```
staleness_score = 1 - decay_function(days_since_last_update)
decay_function(d) = exp(-lambda * d)
lambda = 0.005  (configurable; ~50% decay at ~140 days)
```

This is an explainable, parameterized formula — not a black box.
