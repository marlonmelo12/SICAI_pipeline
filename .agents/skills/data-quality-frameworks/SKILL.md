---
name: data-quality-frameworks
description: Comprehensive data quality validation, testing, and observability frameworks. Enforces automated assertions, schema validation, data profiling, anomaly detection, and integration of tools like Great Expectations, Soda Core, and Pandera into data pipelines.
license: Apache-2.0
---

# Data Quality Frameworks: Validation, Testing & Reliability

Act as a Principal Data Quality & Reliability Engineer. You ensure that every piece of data traversing the platform satisfies strict integrity, validity, timeliness, and completeness standards. In high-assurance domains like digital forensics, you enforce zero tolerance for silent data corruption.

---

## 1. The 6 Pillars of Data Quality

1. **Completeness:** Ensure mandatory fields (e.g., `event_id`, `evidence_id`, `timestamp`, `hash`) are never null or missing.
2. **Uniqueness:** Eliminate unwanted duplicates across natural keys and cryptographic hashes.
3. **Validity:** Enforce adherence to defined formats, domains, regex patterns, and data types.
4. **Consistency:** Ensure cross-table and temporal consistency (e.g., `event_timestamp <= ingested_timestamp`).
5. **Integrity (Referential & Cryptographic):** Foreign key relationships are preserved, and cryptographic checksums match bitwise evidence.
6. **Timeliness:** Detect staleness, pipeline backpressure, and late-arriving records.

---

## 2. Tooling Selection Guide

| Need | Recommended Tool | Execution Point | Primary Benefit |
| :--- | :--- | :--- | :--- |
| **In-memory worker validation** | **Pandera** | Worker Python script / Micro-batch | Type hinting, runtime DataFrame contract enforcement |
| **Declarative pipeline checks** | **Soda Core** | Airflow tasks, CI/CD, post-ETL | Lightweight YAML checks, fast SQL execution |
| **Enterprise test suites & docs**| **Great Expectations (GX)**| Batch reconciliation, certification | Rich profiling, HTML Data Docs for audit |
| **SQL Transformation Tests** | **dbt test** | Model build time | In-warehouse assertions with zero extra infra |

---

## 3. Declarative Soda Core Quality Contract Example

```yaml
# checks_forensic_events.yml
checks for silver_forensic_events:
  # Completeness
  - missing_count(event_id) = 0
  - missing_count(case_id) = 0
  - missing_count(evidence_id) = 0
  - missing_count(event_timestamp) = 0

  # Uniqueness
  - duplicate_count(event_id) = 0

  # Validity & Domain
  - invalid_count(event_type) = 0:
      valid values: ['FILE_ACCESS', 'PROCESS_START', 'CUSTODY_TRANSFER', 'NETWORK_CONN', 'HASH_VERIFY']
  
  # Temporal Consistency (No time travelers)
  - failed rows:
      name: Temporal consistency check
      fail query: |
        SELECT event_id, event_timestamp, ingested_at
        FROM silver_forensic_events
        WHERE event_timestamp > CURRENT_TIMESTAMP + INTERVAL '1 hour'
           OR event_timestamp < TIMESTAMP '1970-01-01 00:00:00'

  # Cryptographic Integrity
  - missing_count(raw_hash_sha256) = 0
  - invalid_count(raw_hash_sha256) = 0:
      valid regex: '^[a-fA-F0-9]{64}$'
```

---

## 4. In-Memory Validation with Pandera

```python
import pandera.polars as pa
import polars as pl

class ForensicEventSchema(pa.DataFrameModel):
    event_id: str = pa.Field(unique=True, nullable=False)
    case_id: str = pa.Field(nullable=False)
    evidence_id: str = pa.Field(nullable=False)
    event_type: str = pa.Field(isin=["FILE_ACCESS", "CUSTODY_TRANSFER", "PROCESS_START"])
    event_timestamp: pl.Datetime = pa.Field(nullable=False)
    hash_sha256: str = pa.Field(str_matches=r"^[a-fA-F0-9]{64}$", nullable=False)

    class Config:
        strict = True  # Reject unexpected columns

# Runtime execution inside worker
def validate_batch(df: pl.DataFrame) -> pl.DataFrame:
    return ForensicEventSchema.validate(df)
```

---

## 5. Circuit Breaker Strategy

- **Critical Failures (Hard Stop):** Hash mismatch, null primary keys, unparseable custody log -> Halt pipeline, emit alert, quarantine partition to DLQ.
- **Warning / Non-blocking (Soft Alert):** Minor schema drift (new optional fields), spike in uncommon event types -> Log warning, write to quarantine table for review, notify data steward.
