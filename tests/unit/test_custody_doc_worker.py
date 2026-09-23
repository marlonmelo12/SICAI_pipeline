# tests/unit/test_custody_doc_worker.py
import pytest
import os
from src.workers.custody_doc_worker import CustodyDocumentWorker

AUTO_APREENSAO = r"C:\Users\marlo\Downloads\SICAI\Vernix\PROCESSO\Samsung J5 - Auto Apreensão.pdf"
LAUDO_OFICIAL = r"C:\Users\marlo\Downloads\SICAI\Vernix\PROCESSO\Samsung J5 - Laudo nº 155.263-2022.pdf"

def test_parse_auto_apreensao():
    if not os.path.exists(AUTO_APREENSAO):
        pytest.skip("Arquivo Auto de Apreensão não encontrado")

    worker = CustodyDocumentWorker(case_id="case_vernix", evidence_id="ev_j5", tenant_id="tenant_sp")
    event = worker.parse_auto_apreensao(AUTO_APREENSAO)

    assert event["stage"] == "COLETA"
    assert "2021-12-08" in event["event_timestamp"]
    assert event["seal_number"] is not None
    assert "31/2021" in event["document_reference"]
    print("\n[TEST PASS] Marco de apreensão extraído com sucesso:", event["event_timestamp"])

def test_parse_laudo_oficial():
    if not os.path.exists(LAUDO_OFICIAL):
        pytest.skip("Arquivo Laudo Oficial não encontrado")

    worker = CustodyDocumentWorker(case_id="case_vernix", evidence_id="ev_j5", tenant_id="tenant_sp")
    event = worker.parse_laudo_oficial(LAUDO_OFICIAL)

    assert event["stage"] == "PROCESSAMENTO"
    assert "2022-05-18" in event["event_timestamp"]
    assert "155.263/2022" in event["document_reference"]
    print("\n[TEST PASS] Marco de exame pericial oficial extraído com sucesso:", event["document_reference"])
