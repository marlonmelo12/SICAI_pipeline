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


# =====================================================================
# Modelos Pydantic para Extração Estruturada via LLM (Qwen 2.5)
# =====================================================================
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class CustodyActionExtraction(BaseModel):
    """
    Modelo representativo de um evento de cadeia de custódia (art. 158-B CPP)
    extraído por LLM de peças processuais ou laudos periciais.
    """
    actor_name: str = Field(..., description="Nome completo do servidor, perito, delegado ou autoridade")
    actor_role: str = Field(..., description="Cargo normatizado: DELEGADO, PERITO_CRIMINAL, ESCRIVAO, JUIZ, PROMOTOR, etc.")
    agency: str = Field(..., description="Órgão de lotação: Polícia Civil, PEFOCE, Instituto de Criminalística, etc.")
    stage_cpp: str = Field(
        ...,
        description="Fase legal da cadeia de custódia (CPP art. 158-B): RECONHECIMENTO, ISOLAMENTO, FIXACAO, COLETA, RECEBIMENTO, TRANSPORTE, PROCESSAMENTO, ARMAZENAMENTO ou DESCARTE"
    )
    action_description: str = Field(..., description="Descrição objetiva da ação pericial ou policial executada")
    seal_number: Optional[str] = Field(None, description="Número do lacre rompido, verificado ou aplicado, se houver")
    event_timestamp: Optional[str] = Field(None, description="Data e hora do evento em formato ISO-8601 ou AAAA-MM-DD")
    page_number: int = Field(..., ge=1, description="Número da página do documento PDF de onde a informação foi extraída")
    verbatim_quote: str = Field(..., min_length=5, description="Citação textual literal e exata da página que comprova a extração (Ground Truth)")

    def verify_ground_truth(self, page_text: str) -> bool:
        """
        Verifica se a citação literal 'verbatim_quote' existe de fato no texto da página original.
        Impede 100% de alucinação de entidades inventadas pela LLM.
        """
        if not self.verbatim_quote:
            return False
        
        # Normalização simples de espaços e pontuação para tolerar quebras de linha no PDF
        import re
        norm_quote = re.sub(r'\s+', ' ', self.verbatim_quote).strip().lower()
        norm_page = re.sub(r'\s+', ' ', page_text).strip().lower()
        return norm_quote in norm_page


class CustodyDocumentExtractionResult(BaseModel):
    """
    Envelope de resultados extraídos para uma peça processual completa.
    """
    document_name: str
    total_pages_analyzed: int
    events: List[CustodyActionExtraction] = Field(default_factory=list)

