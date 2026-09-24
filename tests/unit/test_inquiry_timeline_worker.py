# tests/unit/test_inquiry_timeline_worker.py
import pytest
import os
import pandas as pd
from src.quality.schemas import (
    InquiryActor,
    InquiryChronologicalEvent,
    InquiryTimelineReport,
    InquiryTimelineSchema
)
from src.workers.llm_timeline_worker import (
    LLMInquiryTimelineWorker,
    MockTimelineEngine,
    parse_brazilian_date
)
from src.reporting.timeline_html_generator import generate_interactive_timeline_html

def test_parse_brazilian_date():
    assert parse_brazilian_date("2021-09-20") == "2021-09-20"
    assert parse_brazilian_date("São Paulo, 20 de setembro de 2021.") == "2021-09-20"
    assert parse_brazilian_date("Data da apreensão: 08/12/2021 às 09:28") == "2021-12-08"
    assert parse_brazilian_date("No dia 15 de março de 2020 foi expedido mandado") == "2020-03-15"
    assert parse_brazilian_date("texto sem data nenhuma aqui") is None

def test_ground_truth_verification():
    page_text = """
    ESTADO DE SÃO PAULO - POLÍCIA CIVIL
    Aos 20 de setembro de 2021, nesta cidade de Presidente Venceslau,
    o Delegado Dr. EDMAR ROGÉRIO DIAS CAPARROZ determinou a instauração
    do inquérito policial e cumprimento de mandados.
    """
    valid_event = InquiryChronologicalEvent(
        event_date="2021-09-20",
        raw_date_text="20 de setembro de 2021",
        event_type="INSTAURACAO",
        headline="Instauração de Inquérito Policial",
        description="Instauração determinada pelo Delegado",
        actors=[InquiryActor(name="EDMAR ROGÉRIO DIAS CAPARROZ", role="DELEGADO")],
        page_number=1,
        verbatim_quote="o Delegado Dr. EDMAR ROGÉRIO DIAS CAPARROZ determinou a instauração"
    )
    assert valid_event.verify_ground_truth(page_text) is True

    fake_event = InquiryChronologicalEvent(
        event_date="2021-09-20",
        event_type="INSTAURACAO",
        headline="Fato inexistente",
        description="Juiz determinou prisão preventiva imediatamente",
        page_number=1,
        verbatim_quote="Juiz Federal determinou a prisão preventiva em audiência de custódia"
    )
    assert fake_event.verify_ground_truth(page_text) is False

def test_inquiry_timeline_worker_chronological_ordering():
    worker = LLMInquiryTimelineWorker(case_id="case_test_01", engine=MockTimelineEngine())
    
    # Duas páginas em ordem não cronológica propositalmente
    pages = [
        {
            "page_number": 2,
            "text": "Aos 08 de dezembro de 2021 foi lavrado auto de exibição e apreensão com lacre 0011616 pelo Delegado EDMAR ROGERIO CAPARROZ."
        },
        {
            "page_number": 1,
            "text": "Aos 20 de setembro de 2021 portaria de instauração de inquérito pelo Delegado EDMAR ROGERIO DIAS CAPARROZ."
        }
    ]

    report = worker.process_pages(pages, document_name="inquerito_teste.pdf")
    assert len(report.events) >= 2
    # O primeiro evento ordenado deve ser a data anterior (2021-09-20)
    assert report.events[0].event_date == "2021-09-20"
    assert report.events[1].event_date == "2021-12-08"

def test_extract_actors_graph():
    worker = LLMInquiryTimelineWorker(case_id="case_test_01", engine=MockTimelineEngine())
    pages = [
        {
            "page_number": 1,
            "text": "Aos 20 de setembro de 2021 portaria de instauração de inquérito pelo Delegado EDMAR ROGERIO DIAS CAPARROZ."
        },
        {
            "page_number": 2,
            "text": "Aos 08 de dezembro de 2021 apreensão de bens com lacre de CIRO CESAR LEMOS pelo Delegado EDMAR ROGERIO CAPARROZ."
        }
    ]
    report = worker.process_pages(pages, document_name="inquerito_teste.pdf")
    actors = worker.extract_actors_graph(report)

    assert "EDMAR ROGERIO DIAS CAPARROZ" in actors or "EDMAR ROGERIO CAPARROZ" in actors
    assert len(actors) >= 2

def test_inquiry_timeline_schema_validation(tmp_path):
    worker = LLMInquiryTimelineWorker(case_id="case_test_01", engine=MockTimelineEngine())
    pages = [
        {
            "page_number": 1,
            "text": "Aos 20 de setembro de 2021 portaria de instauração pelo Delegado EDMAR ROGERIO DIAS CAPARROZ."
        }
    ]
    report = worker.process_pages(pages, document_name="inquerito_teste.pdf")
    records = worker.to_dataframe_records(report, ingestion_id="test_ingest_001")
    df = pd.DataFrame(records)

    validated_df = InquiryTimelineSchema.validate(df)
    assert len(validated_df) == len(records)
    assert "event_id" in validated_df.columns
    assert "actors_json" in validated_df.columns

def test_generate_interactive_timeline_html(tmp_path):
    worker = LLMInquiryTimelineWorker(case_id="case_test_01", engine=MockTimelineEngine())
    pages = [
        {
            "page_number": 1,
            "text": "Aos 20 de setembro de 2021 portaria de instauração pelo Delegado EDMAR ROGERIO DIAS CAPARROZ."
        }
    ]
    report = worker.process_pages(pages, document_name="inquerito_teste.pdf")
    actors = worker.extract_actors_graph(report)

    out_file = str(tmp_path / "timeline.html")
    generate_interactive_timeline_html(report, actors, out_file)

    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        html = f.read()
    assert "SICAI FORENSIC AI" in html
    assert "EDMAR ROGERIO DIAS CAPARROZ" in html
