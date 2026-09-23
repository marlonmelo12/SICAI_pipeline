---
name: dbt-transformation-patterns
description: Standards and design patterns for data transformation with dbt (data build tool). Enforces modular dimensional and lakehouse modeling (staging, intermediate, marts), materialization strategies (incremental, table, view), custom macros, testing, and documentation.
license: Apache-2.0
---

# dbt Transformation Patterns: Lakehouse Modeling & Engineering

Act as a Lead Analytics Engineer and dbt Architect. You build modular, performant, DRY, and well-tested SQL transformation pipelines on Lakehouse engines (Trino / DuckDB / Spark / PostgreSQL). You maintain strict separation of concerns, enforce data contracts, and optimize incremental materializations.

---

## 1. Project Layering Structure

```text
models/
├── staging/            # Stg: 1-to-1 with raw/bronze tables, schema renaming, type casting
│   ├── forensics/
│   │   ├── _stg_forensics__sources.yml
│   │   └── stg_forensics__raw_events.sql
├── intermediate/       # Int: Canonical modeling, business joins, entity resolutions
│   └── forensics/
│       ├── _int_forensics__models.yml
│       └── int_forensic_events_normalized.sql
└── marts/              # Marts (Gold): Dimensional models, fact tables, ML feature matrices
    ├── core/
    │   ├── dim_custody_agents.sql
    │   └── fct_case_timeline_events.sql
    └── audit/
        └── fct_custody_chain_integrity.sql
```

---

## 2. Layering Principles & Coding Conventions

### Staging (`stg_`)
- Clean, cast, and rename columns to canonical naming standards (`snake_case`, clear suffixes like `_at` for timestamps, `_id` for identifiers, `is_` for booleans).
- Do NOT perform complex joins, aggregations, or business calculations in staging.
- Set materialization to `view` (or ephemeral).

### Intermediate (`int_`)
- Combine multiple sources into canonical entity models.
- Apply standard forensic event deduplication:
```sql
with ranked_events as (
    select
        *,
        row_number() over (
            partition by evidence_id, source_event_hash 
            order by ingested_at desc
        ) as rn
    from {{ ref('stg_forensics__raw_events') }}
)
select * from ranked_events where rn = 1
```

### Marts (`fct_` and `dim_`)
- Optimize for downstream query performance (Star Schema, wide flattened views for ML/search).
- Materialize as `table` or `incremental`.

---

## 3. Incremental Materialization with Iceberg/Parquet

Always use robust `is_incremental()` logic with a lookback window to account for late-arriving events:

```sql
{{ config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
) }}

select
    event_id,
    case_id,
    evidence_id,
    event_type,
    event_timestamp,
    actor_id,
    ingested_at
from {{ ref('int_forensic_events_normalized') }}

{% if is_incremental() %}
    -- 3-day lookback window for late arrivals
    where ingested_at >= (select dateadd(day, -3, max(ingested_at)) from {{ this }})
{% endif %}
```

---

## 4. Data Contracts & Schema Enforcement

Enforce contracts on public models consumed by downstream applications:

```yaml
version: 2
models:
  - name: fct_case_timeline_events
    config:
      contract:
        enforced: true
    columns:
      - name: event_id
        data_type: string
        constraints:
          - type: not_null
          - type: primary_key
      - name: case_id
        data_type: string
        constraints:
          - type: not_null
      - name: event_timestamp
        data_type: timestamp
        constraints:
          - type: not_null
```

---

## 5. Testing & Validation Strategy

- Built-in tests on every primary key: `unique`, `not_null`.
- Referential integrity tests: `relationships` to ensure `case_id` exists in `dim_cases`.
- Business rules: use `dbt-expectations` for distribution and value range checks.
