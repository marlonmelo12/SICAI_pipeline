# scripts/test_llm_pipeline.py
"""
Script de Teste e Validação da Extração Forense com IA (Qwen 2.5 / LLMCustodyWorker).
Analisa documentos reais de custódia e exibe no terminal os atores, cargos, lacres
e citações literais detectadas, validando a camada Silver do Lakehouse.
"""
import os
import sys
import json
import logging
from pprint import pprint

# Configura o path para encontrar o pacote src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.workers.llm_custody_worker import (
    LLMCustodyWorker,
    OllamaQwenEngine,
    MockQwenEngine
)
from src.lakehouse.storage import LakehouseStorageWriter
import pandas as pd
from src.quality.schemas import CustodyEventSchema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SICAI.TestLLM")

def main():
    print("=" * 70)
    print("   SICAI - TESTE DE DETECÇÃO FORENSE COM IA (QWEN 2.5)   ")
    print("=" * 70)

    # 1. Verifica conectividade com o Ollama (GPU)
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model_name = os.getenv("LLM_MODEL_NAME", "qwen2.5:7b-instruct")
    
    ollama = OllamaQwenEngine(host=ollama_host, model_name=model_name)
    is_gpu_active = ollama.is_available()

    if is_gpu_active:
        print(f"[STATUS] \033[92mOllama Conectado com Sucesso!\033[0m")
        print(f" - Endpoint: {ollama_host}")
        print(f" - Modelo:   {model_name}")
        engine = ollama
    else:
        print(f"[STATUS] \033[93mOllama offline em {ollama_host}.\033[0m")
        print(" - Operando em modo contingência (MockQwenEngine) para demonstrar o fluxo.")
        engine = MockQwenEngine()

    # 2. Localiza o documento pericial para teste
    pdf_target = "Vernix/PROCESSO/Samsung J5 - Auto Apreensão.pdf"
    if len(sys.argv) > 1:
        pdf_target = sys.argv[1]

    if not os.path.exists(pdf_target):
        print(f"\n[ERRO] Arquivo PDF não encontrado: {pdf_target}")
        print("Certifique-se de que a pasta 'Vernix/' está na raiz do projeto.")
        sys.exit(1)

    print(f"\n[DOCUMENTO EM ANÁLISE]: {pdf_target}")
    
    # 3. Inicializa o Worker de IA
    worker = LLMCustodyWorker(
        case_id="case_vernix_01",
        evidence_id="samsung_sm_j510mn",
        tenant_id="policia_civil_sp",
        engine=engine
    )

    # 4. Executa a extração
    print("==> Executando inferência e extração estruturada...")
    extraction_result = worker.process_pdf(pdf_target, max_pages=3)

    print(f"\n" + "-" * 70)
    print(f" RESULTADO DA EXTRAÇÃO (Páginas analisadas: {extraction_result.total_pages_analyzed})")
    print(f" Total de eventos de custódia detectados: {len(extraction_result.events)}")
    print("-" * 70)

    if not extraction_result.events:
        print("Nenhum marco formal de custódia foi identificado nesta peça.")
        return

    # 5. Exibe os dados detectados
    for idx, event in enumerate(extraction_result.events, 1):
        print(f"\n[EVENTO #{idx}]")
        print(f" 👤 Autoridade / Ator:    {event.actor_name}")
        print(f" 💼 Cargo / Função:       {event.actor_role}")
        print(f" 🏢 Órgão / Lotação:      {event.agency}")
        print(f" ⚖️ Etapa CPP (Art. 158-B): {event.stage_cpp}")
        print(f" 🏷️ Lacre Identificado:   {event.seal_number or 'Não mencionado'}")
        print(f" 📅 Data / Hora:          {event.event_timestamp or 'Não informada'}")
        print(f" 📄 Página de Origem:     Página {event.page_number}")
        print(f" 🔍 Ação Executada:       {event.action_description}")
        print(f" 📜 CITAÇÃO LITERAL (GROUND TRUTH):")
        print(f"    \"{event.verbatim_quote}\"")

    # 6. Gravação na Camada Silver (Lakehouse Parquet)
    print("\n" + "=" * 70)
    print(" PERSISTÊNCIA NA CAMADA SILVER (silver.custody_events)")
    print("=" * 70)

    records = worker.to_custody_event_records(extraction_result, ingestion_id="test_ingest_001")
    df = pd.DataFrame(records)

    # Validação do Contrato Pandera
    validated_df = CustodyEventSchema.validate(df)
    print(f" - Contrato Pandera: \033[92mVALIDADO (100% em conformidade com o Lakehouse)\033[0m")

    storage = LakehouseStorageWriter(root_dir="data/lakehouse")
    write_res = storage.write_dataset_partitioned(
        df=validated_df,
        layer="silver",
        table_name="custody_events",
        partition_keys={
            "tenant_id": "policia_civil_sp",
            "case_id": "case_vernix_01",
            "evidence_id": "samsung_sm_j510mn"
        },
        mode="overwrite"
    )

    print(f" - Arquivo Parquet gravado: {write_res['file_path']}")
    print(f" - Registros gravados:      {write_res['records_written']}")
    print(f" - Tamanho do arquivo:      {write_res['bytes_written']} bytes")
    print(f" - Hash SHA-256 do Parquet: {write_res['sha256']}")
    print("\n\033[92m[SUCESSO] Pipeline de IA e Lakehouse testado e validado com sucesso!\033[0m\n")

if __name__ == "__main__":
    main()
