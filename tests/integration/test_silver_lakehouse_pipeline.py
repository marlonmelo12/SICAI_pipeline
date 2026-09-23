# tests/integration/test_silver_lakehouse_pipeline.py
import pytest
import os
import shutil
import tempfile
import pyarrow.parquet as pq
from src.pipelines.silver_pipeline import SilverLakehousePipeline
from src.lakehouse.storage import LakehouseStorageWriter

UFDR_PATH = r"C:\Users\marlo\Downloads\SICAI\Vernix\DADO BRUTO\Samsung SM-J510MN Galaxy J5 Metal.ufdr"
AUTO_APREENSAO = r"C:\Users\marlo\Downloads\SICAI\Vernix\PROCESSO\Samsung J5 - Auto Apreensão.pdf"
LAUDO_OFICIAL = r"C:\Users\marlo\Downloads\SICAI\Vernix\PROCESSO\Samsung J5 - Laudo nº 155.263-2022.pdf"

def test_silver_pipeline_vernix_materialization():
    """
    Testa a materialização completa das 3 tabelas Silver em formato Parquet no Lakehouse:
    1. silver.forensic_artifacts (catálogo de 12.115 arquivos)
    2. silver.forensic_events (mensagens de chat, ligações, eventos de tela)
    3. silver.custody_events (marcos de apreensão e laudo oficial)
    """
    if not os.path.exists(UFDR_PATH) or not os.path.exists(AUTO_APREENSAO):
        pytest.skip("Arquivos reais da Operação Vérnix não encontrados")

    temp_lakehouse_root = tempfile.mkdtemp(prefix="sicai_silver_integration_")
    try:
        writer = LakehouseStorageWriter(root_dir=temp_lakehouse_root)
        pipeline = SilverLakehousePipeline(storage_writer=writer)

        results = pipeline.run_pipeline(
            tenant_id="tenant_sp",
            case_id="case_vernix",
            evidence_id="ev_samsung_j5",
            ufdr_path=UFDR_PATH,
            auto_apreensao_pdf=AUTO_APREENSAO,
            laudo_oficial_pdf=LAUDO_OFICIAL
        )

        assert results["status"] == "SUCCESS"
        assert results["metrics"]["artifacts_count"] == 12115
        assert results["metrics"]["events_count"] > 300
        assert results["metrics"]["custody_events_count"] >= 2
        print("\n[SILVER PIPELINE METRICS]:")
        for k, v in results["metrics"].items():
            print(f"  - {k}: {v}")

        # Validação física de leitura dos arquivos Parquet gerados
        part_keys = {"tenant_id": "tenant_sp", "case_id": "case_vernix", "evidence_id": "ev_samsung_j5"}
        
        # 1. Valida forensic_artifacts
        table_artifacts = writer.read_dataset_partition("silver", "forensic_artifacts", part_keys)
        assert table_artifacts.num_rows == 12115
        assert "file_path" in table_artifacts.column_names
        assert "sha256" in table_artifacts.column_names
        assert "modified_at" in table_artifacts.column_names

        # 2. Valida forensic_events
        table_events = writer.read_dataset_partition("silver", "forensic_events", part_keys)
        assert table_events.num_rows > 300
        assert "event_category" in table_events.column_names
        assert "content_summary" in table_events.column_names

        # 3. Valida custody_events
        table_custody = writer.read_dataset_partition("silver", "custody_events", part_keys)
        assert table_custody.num_rows >= 2
        assert "stage" in table_custody.column_names
        assert "seal_number" in table_custody.column_names
        assert "document_reference" in table_custody.column_names

        print("\n[VALIDAÇÃO FISICA DOS PARQUETS COMMITADOS COM SUCESSO]")
        for tbl_name in ["forensic_artifacts", "forensic_events", "custody_events"]:
            res = results["tables"][tbl_name]
            print(f" -> Tabela {tbl_name}: {res['records_written']} linhas, {res['bytes_written']} bytes gravados (SHA256: {res['sha256'][:16]}...)")
    finally:
        shutil.rmtree(temp_lakehouse_root, ignore_errors=True)
