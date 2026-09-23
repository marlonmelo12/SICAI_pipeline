# tests/unit/test_llm_custody_worker.py
import os
import pytest
import pandas as pd
from src.quality.schemas import CustodyActionExtraction, CustodyEventSchema
from src.workers.llm_custody_worker import (
    MockQwenEngine,
    OllamaQwenEngine,
    LLMCustodyWorker
)

SAMPLE_PAGE_TEXT = """
POLÍCIA CIVIL DO ESTADO DE SÃO PAULO
DELEGACIA DE POLÍCIA DE PRESIDENTE VENCESLAU
BOLETIM DE OCORRÊNCIA Nº: 31/2021
AUTO DE EXIBIÇÃO E APREENSÃO
Aos oito dias do mês de dezembro de 2021, nesta cidade de Presidente Venceslau,
o Escrivão de Polícia recebeu o aparelho Samsung Galaxy J5, sendo devidamente
acondicionado no envelope sob LACRE - 0011634.
"""

def test_pydantic_schema_and_ground_truth():
    # Evento verídico com citação presente no texto
    valid_event = CustodyActionExtraction(
        actor_name="Escrivão de Polícia",
        actor_role="ESCRIVAO",
        agency="Polícia Civil",
        stage_cpp="COLETA",
        action_description="Acondicionamento do celular apreendido",
        seal_number="0011634",
        event_timestamp="2021-12-08T09:28:00-03:00",
        page_number=1,
        verbatim_quote="acondicionado no envelope sob LACRE - 0011634"
    )
    assert valid_event.verify_ground_truth(SAMPLE_PAGE_TEXT) is True

    # Evento com citação alucinada (não existente no texto)
    hallucinated_event = CustodyActionExtraction(
        actor_name="Juiz Inexistente",
        actor_role="JUIZ",
        agency="Tribunal de Justiça",
        stage_cpp="RECEBIMENTO",
        action_description="Recebeu em juízo",
        seal_number="999999",
        page_number=1,
        verbatim_quote="o juiz determinou a remessa ao tribunal federal de brasília"
    )
    assert hallucinated_event.verify_ground_truth(SAMPLE_PAGE_TEXT) is False

def test_mock_qwen_engine_extraction():
    engine = MockQwenEngine()
    events = engine.extract_from_text(SAMPLE_PAGE_TEXT, page_number=1)
    
    assert len(events) >= 1
    event = events[0]
    assert event.stage_cpp == "COLETA"
    assert event.seal_number == "0011634"
    assert event.page_number == 1
    assert event.verify_ground_truth(SAMPLE_PAGE_TEXT) is True

def test_ollama_engine_offline_resilience():
    # Endpoint inacessível deve falhar silenciosamente sem quebrar o pipeline
    offline_engine = OllamaQwenEngine(host="http://localhost:99999", timeout=1)
    assert offline_engine.is_available() is False
    events = offline_engine.extract_from_text(SAMPLE_PAGE_TEXT, page_number=1)
    assert events == []

def test_llm_custody_worker_with_real_pdf():
    pdf_path = "Vernix/PROCESSO/Samsung J5 - Auto Apreensão.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"Arquivo {pdf_path} não encontrado no ambiente de teste")

    worker = LLMCustodyWorker(
        case_id="case_vernix_01",
        evidence_id="samsung_j5",
        tenant_id="policia_civil_sp",
        engine=MockQwenEngine()
    )

    result = worker.process_pdf(pdf_path, max_pages=1)
    assert result.total_pages_analyzed == 1
    assert len(result.events) >= 1

    records = worker.to_custody_event_records(result, ingestion_id="ingest_test_llm")
    assert len(records) >= 1
    
    # Validação do Contrato Pandera de Custódia
    df = pd.DataFrame(records)
    validated_df = CustodyEventSchema.validate(df)
    assert len(validated_df) >= 1
    assert validated_df["evidence_id"].iloc[0] == "samsung_j5"
    assert validated_df["tenant_id"].iloc[0] == "policia_civil_sp"
    assert "Citação:" in validated_df["notes"].iloc[0]
