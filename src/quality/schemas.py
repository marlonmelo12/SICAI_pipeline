# src/quality/schemas.py
"""
Modelos de Contratos de Dados em Pandera para Validação em Tempo de Execução na Camada Silver.
Garante completude, integridade referencial e sanidade de tipos antes da persistência no Lakehouse.
"""
import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional

class ForensicArtifactSchema(pa.DataFrameModel):
    artifact_id: Series[str] = pa.Field(nullable=False)
    tenant_id: Series[str] = pa.Field(nullable=False)
    case_id: Series[str] = pa.Field(nullable=False)
    evidence_id: Series[str] = pa.Field(nullable=False)
    file_path: Series[str] = pa.Field(nullable=False)
    file_name: Series[str] = pa.Field(nullable=False)
    size_bytes: Series[int] = pa.Field(ge=0)
    deleted_status: Series[str] = pa.Field(isin=["Intact", "Deleted", "Carved", "Unknown"])
    modified_at: Series[str] = pa.Field(nullable=True)
    created_at: Series[str] = pa.Field(nullable=True)
    accessed_at: Series[str] = pa.Field(nullable=True)
    sha256: Series[str] = pa.Field(nullable=True)
    md5: Series[str] = pa.Field(nullable=True)
    inode: Series[str] = pa.Field(nullable=True)
    ingestion_id: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = False  # Permite campos auxiliares sem rejeição
        coerce = True

class ForensicEventSchema(pa.DataFrameModel):
    event_id: Series[str] = pa.Field(nullable=False)
    tenant_id: Series[str] = pa.Field(nullable=False)
    case_id: Series[str] = pa.Field(nullable=False)
    evidence_id: Series[str] = pa.Field(nullable=False)
    event_category: Series[str] = pa.Field(
        isin=["MESSAGE", "CALL", "DEVICE", "WEB", "NETWORK", "LOCATION", "APP", "PASSWORD", "OTHER"]
    )
    event_type: Series[str] = pa.Field(nullable=False)
    event_timestamp: Series[str] = pa.Field(nullable=False)
    actor_from: Series[str] = pa.Field(nullable=True)
    actor_to: Series[str] = pa.Field(nullable=True)
    content_summary: Series[str] = pa.Field(nullable=True)
    source_application: Series[str] = pa.Field(nullable=True)
    raw_payload_json: Series[str] = pa.Field(nullable=True)
    ingestion_id: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = False
        coerce = True

class CustodyEventSchema(pa.DataFrameModel):
    event_id: Series[str] = pa.Field(nullable=False)
    tenant_id: Series[str] = pa.Field(nullable=False)
    case_id: Series[str] = pa.Field(nullable=False)
    evidence_id: Series[str] = pa.Field(nullable=False)
    stage: Series[str] = pa.Field(
        isin=[
            "RECONHECIMENTO", "ISOLAMENTO", "FIXACAO", "COLETA",
            "RECEBIMENTO", "TRANSPORTE", "PROCESSAMENTO", "ARMAZENAMENTO", "DESCARTE"
        ]
    )
    event_timestamp: Series[str] = pa.Field(nullable=False)
    actor_name: Series[str] = pa.Field(nullable=False)
    actor_role: Series[str] = pa.Field(nullable=True)
    agency: Series[str] = pa.Field(nullable=False)
    seal_number: Series[str] = pa.Field(nullable=True)
    document_reference: Series[str] = pa.Field(nullable=True)
    notes: Series[str] = pa.Field(nullable=True)
    hash_verified: Series[bool] = pa.Field(nullable=False)
    ingestion_id: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = False
        coerce = True
