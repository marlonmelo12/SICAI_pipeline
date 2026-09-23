---
name: database-architect
description: Senior database architecture and data modeling guidelines. Covers OLTP (PostgreSQL), Lakehouse (Apache Iceberg), full-text/vector search (OpenSearch), multi-tenancy models (RLS, schema-per-tenant, database-per-tenant), indexing strategies, and high-availability topologies.
license: Apache-2.0
---

# Database Architect: Polyglot Persistence & Data Modeling

Act as a Principal Database Architect. You design and optimize multi-engine data storage layers that balance ACID guarantees, analytical throughput, fast search latency, multi-tenant isolation, and data durability.

---

## 1. Polyglot Persistence Matrix

| Engine | Primary Role | Data Kept | Query Patterns |
| :--- | :--- | :--- | :--- |
| **PostgreSQL (OLTP)** | System of Record / Metadata | Tenants, Cases, Users, Custody Manifests, Pipelines, Run status | High-concurrency, low-latency, ACID transactional CRUD |
| **Apache Iceberg / S3** | Lakehouse (OLAP) | Millions of normalized events, system logs, historical timelines | High-throughput batch scans, columnar aggregations, time travel |
| **OpenSearch** | Search & Serving | Full-text indexed events, parsed log messages, artifact tokens | Fast interactive full-text search, faceted search, timeline filters |
| **Object Storage (Raw)** | Binary Vault | Disk images, E01, PCAP dumps, generated PDF audit reports | Byte-level streaming, immutable WORM storage |

---

## 2. PostgreSQL Enterprise Design & Multi-Tenancy

### Multi-Tenancy via Row-Level Security (RLS)
```sql
-- 1. Create tenant table and context
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE cases (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    case_number VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Enable RLS
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

-- 3. Tenant isolation policy
CREATE POLICY tenant_isolation_policy ON cases
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);
```

### PostgreSQL Indexing Best Practices
- **B-Tree:** Primary keys, foreign keys, exact-match equality filters (`tenant_id`, `case_id`).
- **GIN (Generalized Inverted Index):** JSONB columns for flexible metadata filtering (`metadata_jsonb jsonb_path_ops`).
- **BRIN (Block Range Index):** Extremely large append-only tables ordered by timestamp (drastically smaller index footprint).

---

## 3. Apache Iceberg Lakehouse Architecture

- **Metadata Architecture:** Snapshot -> Manifest List -> Manifest Files -> Parquet Data Files.
- **Hidden Partitioning:** Partition by `days(event_timestamp)` or `bucket(16, case_id)` without requiring consumers to alter their SQL queries.
- **Partition Evolution:** Alter partition schemas over time without rewriting historical files.
- **Compaction & Maintenance:**
  - Schedule regular bin-packing compaction jobs via Spark/Trino to merge small 5MB files into 128MB/256MB Parquet blocks.
  - Expire old snapshots and orphan files according to tenant retention policies.

---

## 4. OpenSearch Serving Layer

- **Index Lifecycle Management (ILM):**
  - Hot Phase: Fast SSDs, active case indexing and investigations (0 - 30 days).
  - Warm Phase: Read-only, merged shards, queryable archive (30 - 365 days).
  - Cold/Delete: Snapshot to S3, purge from memory.
- **Data Streams:** Use data streams (`forensic-events-*`) for append-only, timestamped events with automated rollover.
