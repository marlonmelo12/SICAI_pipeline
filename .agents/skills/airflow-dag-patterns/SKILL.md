---
name: airflow-dag-patterns
description: Enterprise Apache Airflow DAG authoring patterns, task design, and orchestration standards. Enforces idempotency, dynamic task mapping, TaskFlow API, custom operators, data-aware scheduling (Datasets), sensor best practices, and robust error recovery.
license: Apache-2.0
---

# Airflow DAG Patterns & Orchestration Standards

Act as a Staff Airflow Engineer. You design clean, maintainable, resilient, and performant DAGs. You enforce modern Airflow 2.x+ idioms (TaskFlow API, dynamic task mapping, Datasets), eliminate scheduler bottlenecks, and guarantee idempotent pipeline execution.

---

## 1. Golden Rules of DAG Authoring

1. **No Heavy Code at Top Level:**
   - Never perform database queries, network calls, filesystem I/O, or heavy imports at the DAG file's top level.
   - The Airflow scheduler executes top-level code every few seconds. Heavy code causes scheduler starvation and CPU spikes.
2. **Deterministic Task Scope:**
   - Tasks must be small, focused, and single-purpose.
   - Do not pass large data structures through XCom (XCom limit is small and backs onto the Airflow metadata DB). Pass storage pointers/URIs instead (`s3://bucket/path/to/data.parquet`).
3. **Idempotency with Execution Dates:**
   - Always parameterize task queries and storage output paths with the logical date (`ds` / `logical_date`).
   - Re-running a DAG run for a specific partition must cleanly overwrite or re-create the data for that partition without corrupting adjacent partitions.

---

## 2. Recommended Patterns

### Pattern A: TaskFlow API (`@task` & `@dag`)
```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task

@dag(
    dag_id="forensic_ingestion_pipeline",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={
        "owner": "data-platform",
        "retries": 3,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
    },
    tags=["forensics", "ingestion", "lakehouse"]
)
def forensic_ingestion():

    @task
    def validate_ingestion_manifest(ingestion_id: str) -> dict:
        return {"ingestion_id": ingestion_id, "status": "VALIDATED", "s3_path": f"s3://bronze/{ingestion_id}/"}

    @task
    def trigger_sandboxed_parser(manifest: dict) -> str:
        silver_dest = f"s3://silver/{manifest['ingestion_id']}/events.parquet"
        return silver_dest

    manifest = validate_ingestion_manifest("uuid-sample-123")
    trigger_sandboxed_parser(manifest)

pipeline = forensic_ingestion()
```

### Pattern B: Dynamic Task Mapping (`.expand()`)
Use `.expand()` when the number of evidences or files to parse is only known at runtime:
```python
@task
def list_pending_evidences(case_id: str) -> list[str]:
    return ["ev_001", "ev_002", "ev_003"]

@task
def process_single_evidence(evidence_id: str) -> dict:
    return {"evidence_id": evidence_id, "processed": True}

evidences = list_pending_evidences("case_456")
process_single_evidence.expand(evidence_id=evidences)
```

### Pattern C: Data-Aware Scheduling (Datasets)
Decouple producer and consumer DAGs using Airflow Datasets:
```python
from airflow.datasets import Dataset

silver_events_dataset = Dataset("s3://lakehouse/silver/forensic_events")

@task(outlets=[silver_events_dataset])
def normalize_and_publish():
    ...

@dag(schedule=[silver_events_dataset], start_date=datetime(2026, 1, 1))
def build_gold_case_timeline():
    ...
```

---

## 3. Sensor Best Practices & Deferrable Operators

- **Always use `mode='reschedule'`:** Never use `mode='poke'` for long waits (> 1 minute). `poke` occupies an Airflow worker slot continuously.
- **Use Deferrable Operators:** Leverage triggerer-based deferrable operators (`TimeDeltaSensorAsync`, `HttpSensorAsync`) to free up workers.

---

## 4. Error Callbacks & Observability

```python
def on_dag_failure(context):
    task_instance = context.get('task_instance')
    exception = context.get('exception')
    emit_audit_alert(task=task_instance.task_id, error=str(exception))

default_args = {
    "on_failure_callback": on_dag_failure,
    "retries": 2,
}
```
