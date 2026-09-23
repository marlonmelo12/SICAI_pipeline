# tests/integration/test_vernix_anomaly_detection.py
import pytest
import os
import datetime
from src.workers.ufdr_parser_worker import UFDRStreamingParser
from src.workers.custody_doc_worker import CustodyDocumentWorker

UFDR_PATH = r"C:\Users\marlo\Downloads\SICAI\Vernix\DADO BRUTO\Samsung SM-J510MN Galaxy J5 Metal.ufdr"
AUTO_APREENSAO = r"C:\Users\marlo\Downloads\SICAI\Vernix\PROCESSO\Samsung J5 - Auto Apreensão.pdf"
LAUDO_OFICIAL = r"C:\Users\marlo\Downloads\SICAI\Vernix\PROCESSO\Samsung J5 - Laudo nº 155.263-2022.pdf"

def test_detect_write_activity_under_police_custody():
    """
    Valida a regra de negócio central do SICAI e do Parecer Técnico do Prof. Marcos Monteiro:
    Identifica arquivos que sofreram modificação (ModifyTime) enquanto o aparelho estava sob custódia estatal.
    """
    if not os.path.exists(UFDR_PATH) or not os.path.exists(AUTO_APREENSAO):
        pytest.skip("Arquivos reais da Operação Vérnix não encontrados")

    # 1. Recupera o marco temporal de apreensão: 08/12/2021 09:28 (UTC-3)
    worker = CustodyDocumentWorker("case_vernix", "ev_j5", "tenant_sp")
    seizure_event = worker.parse_auto_apreensao(AUTO_APREENSAO)
    seizure_dt = datetime.datetime.fromisoformat(seizure_event["event_timestamp"])

    # 2. Recupera o marco final do laudo oficial: 15/06/2022 23:59 (UTC-3)
    official_end_dt = datetime.datetime(2022, 6, 16, tzinfo=datetime.timezone(datetime.timedelta(hours=-3)))

    # 3. Itera sobre os arquivos registrados no UFDR
    parser = UFDRStreamingParser(UFDR_PATH)
    violations = []

    count = 0
    for file_record in parser.iterate_tagged_files():
        count += 1
        mod_at_str = file_record.get("modified_at")
        if not mod_at_str:
            continue

        try:
            # Converte ISO timestamp do XML (ex: 2022-05-18T14:22:10+00:00)
            mod_dt = datetime.datetime.fromisoformat(mod_at_str)
            # Verifica se foi modificado entre a data de apreensão e o fim da perícia oficial
            if seizure_dt < mod_dt <= official_end_dt:
                violations.append({
                    "file_path": file_record["file_path"],
                    "modified_at": mod_at_str,
                    "size_bytes": file_record["size_bytes"],
                    "sha256": file_record["sha256"],
                })
        except Exception:
            continue

    print(f"\n[SICAI ANOMALY ENGINE] Total de arquivos analisados: {count}")
    print(f"[SICAI ANOMALY ENGINE] Arquivos com atividade de escrita durante a custódia policial: {len(violations)}")

    # O Parecer Técnico oficial identificou 379 arquivos modificados na posse da polícia/perito oficial
    assert len(violations) > 0, "Deveria ter detectado arquivos modificados pós-apreensão!"
    print(f"[SICAI ANOMALY ENGINE] Exemplos de arquivos adulterados detectados:")
    for v in violations[:5]:
        print(f"  -> {v['file_path']} (Modificado em: {v['modified_at']})")
