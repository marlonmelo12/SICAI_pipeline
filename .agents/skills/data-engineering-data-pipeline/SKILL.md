---
name: data-engineering-data-pipeline
description: Production-grade data pipeline architecture and implementation patterns. Covers end-to-end ingestion, parsing, extraction, validation, enrichment, and loading with resilience, retry mechanisms, backfill strategies, and SLA monitoring.
license: Apache-2.0
---

# Data Engineering: Pipeline Patterns & Ingestion Architecture

Act as a Senior Data Pipeline Architect. You build robust, fault-tolerant, scalable, and self-healing data pipelines for both batch and event-driven workflows. You prioritize atomic transactions, isolation of parsing logic, dead-letter routing, and full execution auditability.

---

## 1. End-to-End Pipeline Stages

```text
[Dropzone / Stream]
        │
        ▼
┌───────────────┐
│ 1. Ingestion  │  Validate envelope, compute cryptographic hash (SHA-256), store raw manifest
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  2. Parsing   │  Sandboxed worker extraction (TSK, Plaso, custom parsers)
└───────┬───────┘
        │
        ├── [Failure] ──→ Dead Letter Queue (DLQ) + Error Annotation
        │
        ▼ [Success]
┌───────────────┐
│ 3. Validation │  Data quality checks, contract enforcement (Pandera, Great Expectations)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│4. Normalization│ Map to Canonical Forensic Event Model (Silver Iceberg Table)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 5. Enrichment │  GeoIP, threat intel, timeline linking, actor resolution
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 6. Publication│  Commit to Gold / Index into OpenSearch / Publish event.processed
└───────────────┘
```

---

## 2. Ingestion & Pre-Processing Best Practices

1. **Envelope Validation:**
   - Verify file headers, MIME types, and file sizes before allocating parsing compute.
   - Reject or quarantine zero-byte or malformed upload payloads immediately.
2. **Cryptographic Checksum Verification:**
   - Always calculate SHA-256 and SHA-512 hashes at ingestion time.
   - Compare with client-provided hash (if present) to confirm transport integrity.
3. **Storage Manifest Creation:**
   - Generate an immutable manifest detailing:
     - `ingestion_id`: UUIDv4
     - `source_uri`: Origin endpoint or file drop
     - `ingested_at`: UTC timestamp
     - `hash_sha256`: Hexdigest
     - `content_length`: In bytes

---

## 3. Worker Architecture & Sandboxed Parsing

- **Isolate Parsing Logic:** Forensic parsers (e.g., The Sleuth Kit, Plaso, file format decoders) may encounter malformed or adversarial inputs. Run parsers in dedicated containerized worker processes with memory/CPU limits.
- **Streaming & Chunking:** For large forensic disks or image dumps (e.g., raw dd, E01, PCAP), stream chunks rather than loading entire multi-gigabyte files into RAM.
- **Worker Autonomy:** Workers poll tasks from an orchestrator/queue (Airflow / Celery / Kafka), process independently, and push results to staging object storage.

---

## 4. Error Handling & Dead Letter Queue (DLQ)

- Never fail silently or drop records on parsing or validation errors.
- Every rejected payload must be emitted to a DLQ with:
  - `failed_at`: Timestamp
  - `payload_reference`: S3 pointer to raw data
  - `pipeline_step`: e.g., `PARSER_PLASO_V2`
  - `error_message`: Stack trace or schema failure reason
  - `retry_count`: Current retry attempt
- Enable operator UI/APIs to inspect, modify parsing parameters, and replay messages from the DLQ.

---

## 5. Reprocessing & Backfill Protocol

- Reprocessing must never overwrite historical raw data.
- When an updated parser or schema normalization logic is deployed:
  1. Trigger an Airflow backfill DAG specifying the target version (`parser_version=v2.1`).
  2. Write output to a new snapshot/partition in Silver/Gold.
  3. Validate data parity and regression metrics.
  4. Switch consumers or alias references atomically (e.g., Iceberg branch or pointer update).
