# src/pipelines/silver_pipeline.py
"""
Pipeline de Materialização da Camada Silver do Lakehouse SICAI.
Coordena a extração forense, validação de contratos de dados (Pandera) e persistência
colunar particionada em Apache Parquet com garantia de idempotência estrita.
"""
import os
import uuid
import time
import pandas as pd
from typing import Dict, Any, List, Optional
import logging

from src.workers.ufdr_parser_worker import UFDRStreamingParser
from src.workers.custody_doc_worker import CustodyDocumentWorker
from src.workers.llm_custody_worker import LLMCustodyWorker
from src.lakehouse.storage import LakehouseStorageWriter
from src.quality.schemas import ForensicArtifactSchema, ForensicEventSchema, CustodyEventSchema

logger = logging.getLogger("sicai.silver_pipeline")

class SilverLakehousePipeline:
    def __init__(self, storage_writer: Optional[LakehouseStorageWriter] = None):
        self.storage = storage_writer or LakehouseStorageWriter()

    def run_pipeline(
        self,
        tenant_id: str,
        case_id: str,
        evidence_id: str,
        ufdr_path: str,
        auto_apreensao_pdf: Optional[str] = None,
        laudo_oficial_pdf: Optional[str] = None,
        ingestion_id: Optional[str] = None,
        batch_size: int = 5000,
        use_llm: bool = True,
        llm_max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executa a transformação ponta a ponta para popular as 3 tabelas da Camada Silver:
        1. silver.forensic_artifacts
        2. silver.forensic_events
        3. silver.custody_events
        """
        start_time = time.time()
        ingest_id = ingestion_id or str(uuid.uuid4())
        partition_keys = {
            "tenant_id": tenant_id,
            "case_id": case_id,
            "evidence_id": evidence_id
        }

        results = {
            "pipeline": "SILVER_LAKEHOUSE_MATERIALIZATION",
            "ingestion_id": ingest_id,
            "partition": partition_keys,
            "tables": {},
            "metrics": {},
            "status": "STARTED"
        }

        # -------------------------------------------------------------
        # 1. Extração e Persistência de silver.forensic_artifacts
        # -------------------------------------------------------------
        parser = UFDRStreamingParser(ufdr_path)
        artifacts_records = []
        for artifact in parser.iterate_tagged_files(
            tenant_id=tenant_id,
            case_id=case_id,
            evidence_id=evidence_id,
            ingestion_id=ingest_id
        ):
            artifacts_records.append(artifact)

        if artifacts_records:
            df_artifacts = pd.DataFrame(artifacts_records)
            # Validação do Contrato Pandera
            validated_artifacts = ForensicArtifactSchema.validate(df_artifacts)
            # Gravação colunar em Parquet
            write_res = self.storage.write_dataset_partitioned(
                df=validated_artifacts,
                layer="silver",
                table_name="forensic_artifacts",
                partition_keys=partition_keys,
                mode="overwrite"
            )
            results["tables"]["forensic_artifacts"] = write_res
            results["metrics"]["artifacts_count"] = write_res["records_written"]
        else:
            results["metrics"]["artifacts_count"] = 0

        # -------------------------------------------------------------
        # 2. Extração e Persistência de silver.forensic_events
        # -------------------------------------------------------------
        events_records = []
        for event in parser.iterate_decoded_events(
            tenant_id=tenant_id,
            case_id=case_id,
            evidence_id=evidence_id,
            ingestion_id=ingest_id
        ):
            events_records.append(event)

        if events_records:
            df_events = pd.DataFrame(events_records)
            # Validação do Contrato Pandera
            validated_events = ForensicEventSchema.validate(df_events)
            # Gravação colunar em Parquet
            write_res = self.storage.write_dataset_partitioned(
                df=validated_events,
                layer="silver",
                table_name="forensic_events",
                partition_keys=partition_keys,
                mode="overwrite"
            )
            results["tables"]["forensic_events"] = write_res
            results["metrics"]["events_count"] = write_res["records_written"]
        else:
            results["metrics"]["events_count"] = 0

        # -------------------------------------------------------------
        # 3. Extração e Persistência de silver.custody_events
        # -------------------------------------------------------------
        custody_records = []
        custody_worker = CustodyDocumentWorker(case_id=case_id, evidence_id=evidence_id, tenant_id=tenant_id)

        if auto_apreensao_pdf and os.path.exists(auto_apreensao_pdf):
            ev1 = custody_worker.parse_auto_apreensao(auto_apreensao_pdf)
            ev1["event_id"] = str(uuid.uuid4())
            ev1["ingestion_id"] = ingest_id
            custody_records.append(ev1)

        if laudo_oficial_pdf and os.path.exists(laudo_oficial_pdf):
            ev2 = custody_worker.parse_laudo_oficial(laudo_oficial_pdf)
            ev2["event_id"] = str(uuid.uuid4())
            ev2["ingestion_id"] = ingest_id
            custody_records.append(ev2)

        # Enriquecimento com IA (Qwen 2.5 / LLMCustodyWorker)
        if use_llm:
            try:
                llm_worker = LLMCustodyWorker(
                    case_id=case_id,
                    evidence_id=evidence_id,
                    tenant_id=tenant_id
                )
                for pdf_file in [auto_apreensao_pdf, laudo_oficial_pdf]:
                    if pdf_file and os.path.exists(pdf_file):
                        ext_res = llm_worker.process_pdf(pdf_file, max_pages=llm_max_pages)
                        llm_records = llm_worker.to_custody_event_records(ext_res, ingestion_id=ingest_id)
                        custody_records.extend(llm_records)
            except Exception as llm_err:
                logger.warning(f"Processamento LLM de custódia falhou, mantendo extração heurística: {llm_err}")

        if custody_records:
            df_custody = pd.DataFrame(custody_records)
            # Validação do Contrato Pandera
            validated_custody = CustodyEventSchema.validate(df_custody)
            # Gravação colunar em Parquet
            write_res = self.storage.write_dataset_partitioned(
                df=validated_custody,
                layer="silver",
                table_name="custody_events",
                partition_keys=partition_keys,
                mode="overwrite"
            )
            results["tables"]["custody_events"] = write_res
            results["metrics"]["custody_events_count"] = write_res["records_written"]
        else:
            results["metrics"]["custody_events_count"] = 0

        elapsed = time.time() - start_time
        results["metrics"]["elapsed_seconds"] = round(elapsed, 3)
        results["status"] = "SUCCESS"
        return results
