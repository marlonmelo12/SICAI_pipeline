# scripts/process_large_inquiry.py
"""
Pipeline de Processamento Forense para Autos Processuais Massivos (10.000+ páginas).
Utiliza Triagem C++ ultrarrápida (PyMuPDF) em 30s para localizar páginas com vestígios
e Cadeia de Custódia, direcionando apenas as páginas relevantes para a LLM Qwen 2.5 (GPU).
"""
import os
import sys
import time
import re
import argparse
import logging
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from src.workers.llm_custody_worker import (
    LLMCustodyWorker,
    OllamaQwenEngine,
    MockQwenEngine
)
from src.lakehouse.storage import LakehouseStorageWriter
from src.quality.schemas import CustodyEventSchema, CustodyDocumentExtractionResult, CustodyActionExtraction
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SICAI.LargeInquiryProcessor")

DEFAULT_PATTERNS = [
    r'lacre\s*[-–—:]*\s*[0-9]+',
    r'auto\s+de\s+(exibi[cç][aã]o|apreens[aã]o)',
    r'cadeia\s+de\s+cust[oó]dia',
    r'relacra(do|mento|da)',
    r'samsung.*j5',
    r'sm-j510',
    r'0011610',
    r'0011634',
    r'0011616',
    r'laudo\s+(pericial|n[º°]\s*155\.263)'
]

def triage_pages(pdf_path: str, regex_patterns: List[str]) -> List[int]:
    """Varre todas as páginas do PDF em C++ para localizar páginas com relevância forense."""
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) não está instalado. Execute: pip install pymupdf")

    compiled = re.compile("|".join(regex_patterns), re.IGNORECASE)
    matching_pages = []

    t0 = time.time()
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    logger.info(f"Iniciando triagem C++ de alta velocidade em {total_pages} páginas...")

    for i in range(total_pages):
        page_text = doc[i].get_text()
        if compiled.search(page_text):
            matching_pages.append(i + 1)

    elapsed = time.time() - t0
    logger.info(f"Triagem concluída em {elapsed:.2f}s! Identificadas {len(matching_pages)} páginas com potencial probatório entre as {total_pages}.")
    return matching_pages

def main():
    parser = argparse.ArgumentParser(description="SICAI - Processamento Forense de Autos Processuais Massivos")
    parser.add_argument("pdf_path", nargs="?", default="Vernix/PROCESSO/1501022-64.2019.8.26.0483-001.pdf", help="Caminho do arquivo PDF do processo judicial")
    parser.add_argument("--all", action="store_true", help="Processar integralmente todas as páginas probatórias detectadas na triagem")
    parser.add_argument("--max", type=int, default=None, help="Limite máximo de páginas probatórias a processar")
    args = parser.parse_args()

    print("=" * 75)
    print("   SICAI - PROCESSAMENTO DE AUTOS PROCESSUAIS MASSIVOS (IA + GPU)   ")
    print("=" * 75)

    pdf_target = args.pdf_path

    if not os.path.exists(pdf_target):
        print(f"\n[ERRO] Arquivo não encontrado: {pdf_target}")
        sys.exit(1)

    file_size_gb = os.path.getsize(pdf_target) / (1024**3)
    print(f"\n[ARQUIVO]: {pdf_target} ({file_size_gb:.2f} GB)")

    # 1. Triagem de Alta Velocidade (C++)
    matching_pages = triage_pages(pdf_target, DEFAULT_PATTERNS)
    
    if not matching_pages:
        print("[AVISO] Nenhuma página com termos forenses prioritários foi localizada.")
        sys.exit(0)

    print(f"\n[PÁGINAS SELECIONADAS PARA INFERÊNCIA DA IA]:")
    print(f" -> Total: {len(matching_pages)} páginas (Exemplos: {matching_pages[:20]}...)")
    print(f" -> Economia de Computação: {(1 - len(matching_pages)/11783)*100:.1f}% das páginas irrelevantes descartadas antes da LLM.")

    # Suporte a argumentos CLI e variáveis de ambiente
    batch_env = os.getenv("MAX_PAGES_BATCH", "30").strip().lower()

    if args.all or batch_env in ("all", "0", "-1", "none"):
        pages_to_process = matching_pages
        print(f" -> Modo Integral Ativado: Analisando TODAS as {len(pages_to_process)} páginas probatórias com a LLM...")
    else:
        max_batch = args.max if args.max is not None else int(batch_env)
        pages_to_process = matching_pages[:max_batch]
        print(f" -> Processando lote com as {len(pages_to_process)} primeiras páginas probatórias (use --all ou MAX_PAGES_BATCH=all para todas as {len(matching_pages)})...")

    # 2. Conexão com a LLM (Ollama / GPU)
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model_name = os.getenv("LLM_MODEL_NAME", "qwen2.5:7b")
    ollama = OllamaQwenEngine(host=ollama_host, model_name=model_name)

    if ollama.is_available() and ollama.get_installed_models():
        print(f"\n[IA ATIVA NA GPU]: Conectado ao modelo {ollama.model_name} em {ollama_host}")
        engine = ollama
    else:
        print(f"\n[MODO CONTINGÊNCIA]: Ollama offline. Usando MockQwenEngine.")
        engine = MockQwenEngine()

    worker = LLMCustodyWorker(
        case_id="case_vernix_01",
        evidence_id="samsung_sm_j510mn",
        tenant_id="policia_civil_sp",
        engine=engine
    )

    # 3. Processamento das páginas selecionadas
    doc = fitz.open(pdf_target)
    all_events: List[CustodyActionExtraction] = []

    print("\n==> Iniciando Extração Estruturada com Qwen 2.5...")
    start_llm = time.time()

    for idx, page_num in enumerate(pages_to_process, 1):
        print(f" [{idx}/{len(pages_to_process)}] Analisando Página {page_num} com a LLM...")
        page_text = doc[page_num - 1].get_text()
        events = worker.engine.extract_from_text(page_text, page_number=page_num)
        all_events.extend(events)

    llm_elapsed = time.time() - start_llm
    print(f"\n[INFERÊNCIA CONCLUÍDA EM {llm_elapsed:.2f}s]")
    print(f"Total de marcos de custódia detectados nas páginas qualificadas: {len(all_events)}")

    # 4. Exibição dos Marcos Detectados
    print("\n" + "=" * 75)
    print(" RELATÓRIO DE CUSTÓDIA EXTRAÍDO DO PROCESSO PRINCIPAL")
    print("=" * 75)

    for i, ev in enumerate(all_events, 1):
        print(f"\n[MARCO #{i} - PÁGINA {ev.page_number}]")
        print(f" 👤 Autoridade / Ator:    {ev.actor_name} ({ev.actor_role})")
        print(f" 🏢 Lotação:              {ev.agency}")
        print(f" ⚖️ Fase CPP:             {ev.stage_cpp}")
        print(f" 🏷️ Lacre:                {ev.seal_number or 'N/A'}")
        print(f" 📅 Data:                 {ev.event_timestamp or 'N/A'}")
        print(f" 🔍 Ação:                 {ev.action_description}")
        print(f" 📜 Citação:              \"{ev.verbatim_quote}\"")

    # 5. Persistência na Camada Silver
    if all_events:
        res = CustodyDocumentExtractionResult(
            document_name=os.path.basename(pdf_target),
            total_pages_analyzed=len(pages_to_process),
            events=all_events
        )
        records = worker.to_custody_event_records(res, ingestion_id="large_inquiry_ingest_001")
        df = pd.DataFrame(records)
        validated_df = CustodyEventSchema.validate(df)

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
            mode="append"
        )
        print("\n" + "=" * 75)
        print(f" [LAKEHOUSE] {write_res['records_written']} marcos persistidos em:")
        print(f" -> {write_res['file_path']}")
        print("=" * 75)

if __name__ == "__main__":
    main()
