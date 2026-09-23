# src/ingestion/manifest_builder.py
"""
Gerador do Manifesto Imutável de Ingestão do SICAI.
"""
import uuid
import datetime
import os
from typing import Dict, Any, Optional
from src.common.crypto import compute_hashes_streaming

def build_ingestion_manifest(
    tenant_id: str,
    case_id: str,
    evidence_id: str,
    file_path: str,
    operator_name: str = "SYSTEM_INGEST_WORKER",
    source_envelope: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Gera o documento JSON de manifesto contendo metadados completos de integridade e proveniência.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    stat = os.stat(file_path)
    hashes = compute_hashes_streaming(file_path)
    ingestion_id = str(uuid.uuid4())

    manifest = {
        "manifest_version": "1.0.0",
        "ingestion_id": ingestion_id,
        "tenant_id": tenant_id,
        "case_id": case_id,
        "evidence_id": evidence_id,
        "source_filename": os.path.basename(file_path),
        "source_path": os.path.abspath(file_path),
        "size_bytes": stat.st_size,
        "hashes": {
            "sha256": hashes["sha256"],
            "sha512": hashes["sha512"],
            "md5": hashes["md5"],
        },
        "timestamps": {
            "ingested_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "file_modified_at_utc": datetime.datetime.fromtimestamp(stat.st_mtime, datetime.timezone.utc).isoformat(),
            "file_created_at_utc": datetime.datetime.fromtimestamp(stat.st_ctime, datetime.timezone.utc).isoformat(),
        },
        "provenance": {
            "operator": operator_name,
            "system": "SICAI_INGESTION_GATEWAY_V1",
            "storage_layer": "GARAGE_S3_BRONZE",
        },
        "source_envelope": source_envelope or {},
    }
    return manifest
