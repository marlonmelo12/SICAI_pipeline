# scripts/reconstruct_inquiry_timeline.py
"""
SICAI - Reconstituição Cronológica de Fatos e Grafo de Atores Processuais via IA (Qwen 2.5).
Analisa inquéritos policiais e autos judiciais de qualquer dimensão (10.000+ páginas),
reconstrói a cronologia exata dos acontecimentos (datas, decisões, operações, oitivas)
e identifica todas as pessoas físicas envolvidas (Delegados, Juízes, Investigadores, etc.).
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

from src.workers.llm_timeline_worker import (
    LLMInquiryTimelineWorker,
    OllamaTimelineEngine,
    MockTimelineEngine
)
from src.reporting.timeline_html_generator import generate_interactive_timeline_html
from src.lakehouse.storage import LakehouseStorageWriter
from src.quality.schemas import InquiryTimelineSchema
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SICAI.InquiryTimelineReconstructor")

# Padrões de alta precisão para triagem de páginas processuais fáticas
TIMELINE_TRIAGE_PATTERNS = [
    r'portaria\s+de\s+instaura[cç][aã]o',
    r'instaurou-se|instauro\s+o\s+presente',
    r'decis[aã]o\s+interlocut[oó]ria',
    r'defiro\s+o\s+pedido|indefiro\s+o\s+pedido',
    r'mandado\s+de\s+(busca|pris[aã]o)',
    r'busca\s+e\s+apreens[aã]o',
    r'auto\s+de\s+(exibi[cç][aã]o|apreens[aã]o)',
    r'termo\s+de\s+(depoimento|declara[cç][oõ]es|interrogat[oó]rio)',
    r'relat[oó]rio\s+(policial|de\s+investiga[cç][aã]o|final)',
    r'laudo\s+pericial',
    r'ordem\s+de\s+servi[cç]o',
    r'opera[cç][aã]o\s+policial',
    r'of[ií]cio\s+n[oº°]',
    r'den[uú]ncia\s+crime',
    r'cotas?\s+ministeria(l|is)'
]

def triage_inquiry_pages(pdf_path: str, patterns: List[str]) -> List[int]:
    """Varre todas as páginas do processo em C++ identificando marcos fáticos e processuais."""
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) não está instalado. Execute: pip install pymupdf")

    compiled = re.compile("|".join(patterns), re.IGNORECASE)
    matching_pages = []

    t0 = time.time()
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    logger.info(f"Iniciando triagem ultrarrápida C++ em {total_pages} páginas do inquérito...")

    for i in range(total_pages):
        page_text = doc[i].get_text()
        if compiled.search(page_text):
            matching_pages.append(i + 1)

    elapsed = time.time() - t0
    logger.info(f"Triagem C++ finalizada em {elapsed:.2f}s! Encontradas {len(matching_pages)} páginas fáticas entre {total_pages}.")
    return matching_pages

def main():
    parser = argparse.ArgumentParser(description="SICAI - Reconstituição Cronológica de Inquéritos e Grafo de Atores")
    parser.add_argument("pdf_path", nargs="?", default="Vernix/PROCESSO/1501022-64.2019.8.26.0483-001.pdf", help="Caminho do arquivo PDF do inquérito ou processo")
    parser.add_argument("--all", action="store_true", help="Processar todas as páginas fáticas identificadas na triagem")
    parser.add_argument("--max", type=int, default=None, help="Limite máximo de páginas probatórias a processar")
    parser.add_argument("--case-id", default="inquerito_operacao_01", help="Identificador do caso/inquérito")
    parser.add_argument("--html-out", default="data/inquiry_timeline.html", help="Caminho para gerar o painel interativo HTML")
    args = parser.parse_args()

    print("=" * 80)
    print("   SICAI - RECONSTITUIÇÃO CRONOLÓGICA DE INQUÉRITOS & GRAFO DE ATORES (IA)   ")
    print("=" * 80)

    pdf_target = args.pdf_path
    if not os.path.exists(pdf_target):
        print(f"\n[ERRO] Arquivo não encontrado: {pdf_target}")
        sys.exit(1)

    file_size_gb = os.path.getsize(pdf_target) / (1024**3)
    print(f"\n[DOCUMENTO DOS AUTOS]: {pdf_target} ({file_size_gb:.2f} GB)")

    # 1. Triagem C++ de alta velocidade
    probative_pages = triage_inquiry_pages(pdf_target, TIMELINE_TRIAGE_PATTERNS)
    if not probative_pages:
        print("[AVISO] Nenhuma página com atos processuais ou fatos operacionais foi identificada.")
        sys.exit(0)

    # 2. Definição do lote de páginas a submeter à LLM
    batch_env = os.getenv("MAX_PAGES_BATCH", "25").strip().lower()
    if args.all or batch_env in ("all", "0", "-1", "none"):
        pages_to_process = probative_pages
        print(f" -> Modo Integral Ativado: {len(pages_to_process)} páginas fáticas enviadas para a LLM...")
    else:
        max_batch = args.max if args.max is not None else int(batch_env)
        pages_to_process = probative_pages[:max_batch]
        print(f" -> Lote Prioritário: {len(pages_to_process)} páginas fáticas selecionadas (use --all para todas as {len(probative_pages)})...")

    # 3. Conexão com Ollama / GPU
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model_name = os.getenv("LLM_MODEL_NAME", "qwen2.5:7b")
    ollama = OllamaTimelineEngine(host=ollama_host, model_name=model_name)

    if ollama.is_available():
        print(f"\n[MOTOR DE IA ATIVO NA GPU]: Ollama {model_name} em {ollama_host}")
        engine = ollama
    else:
        print(f"\n[MODO CONTINGÊNCIA]: Ollama offline. Usando MockTimelineEngine.")
        engine = MockTimelineEngine()

    worker = LLMInquiryTimelineWorker(case_id=args.case_id, tenant_id="policia_civil_sp", engine=engine)

    # 4. Extração estruturada página por página
    doc = fitz.open(pdf_target)
    pages_content = []
    for p_num in pages_to_process:
        pages_content.append({
            "page_number": p_num,
            "text": doc[p_num - 1].get_text()
        })

    print(f"\n==> Executando Inferência com IA Qwen 2.5 em {len(pages_content)} páginas probatórias...")
    t0 = time.time()
    report = worker.process_pages(pages_content, document_name=os.path.basename(pdf_target))
    elapsed_llm = time.time() - t0

    # 5. Consolidação do Grafo de Atores
    actors_graph = worker.extract_actors_graph(report)

    print(f"\n[PROCESSAMENTO CONCLUÍDO EM {elapsed_llm:.2f}s]")
    print(f" -> Total de Fatos / Decisões na Linha do Tempo: {len(report.events)}")
    print(f" -> Total de Pessoas Físicas / Atores Mapeados:   {len(actors_graph)}")

    # 6. Exibição no Terminal
    print("\n" + "=" * 80)
    print(" CRONOLOGIA DOS FATOS RECONSTITUÍDA (ORDEM TEMPORAL T0 -> Tn)")
    print("=" * 80)

    for i, ev in enumerate(report.events, 1):
        actors_str = ", ".join([f"{a.name} ({a.role})" for a in ev.actors]) if ev.actors else "Não individualizado"
        print(f"\n[MARCO #{i:02d}] 📅 DATA: {ev.event_date or 'Data a apurar'} | Fls. {ev.page_number} | [{ev.event_type}]")
        print(f"  📌 Fato:    {ev.headline}")
        print(f"  📝 Detalhe: {ev.description}")
        print(f"  👥 Atores:  {actors_str}")
        print(f"  📜 Ground Truth: \"{ev.verbatim_quote}\"")

    print("\n" + "=" * 80)
    print(" CATÁLOGO DE ATORES CITADOS NO INQUÉRITO (QUEM É QUEM)")
    print("=" * 80)
    for name, a_info in sorted(actors_graph.items(), key=lambda x: x[1]["appearances_count"], reverse=True):
        roles_str = "/".join(a_info["roles"])
        orgs_str = ", ".join(a_info["organizations"]) if a_info["organizations"] else "N/A"
        dates_str = ", ".join(a_info["dates"][:3])
        print(f" 👤 {name} [{roles_str}] - Órgão: {orgs_str} | Aparições: {a_info['appearances_count']} atos | Fls: {a_info['pages'][:5]}")

    # 7. Geração do Painel Interativo HTML
    os.makedirs(os.path.dirname(args.html_out) or ".", exist_ok=True)
    generate_interactive_timeline_html(report, actors_graph, args.html_out)
    print(f"\n[PAINEL INTERATIVO GERADO COM SUCESSO]")
    print(f" -> Abra no seu navegador: file:///{os.path.abspath(args.html_out).replace(os.sep, '/')}")

    # 8. Persistência no Lakehouse Silver Parquet
    if report.events:
        records = worker.to_dataframe_records(report, ingestion_id=f"inquiry_ingest_{int(time.time())}")
        df = pd.DataFrame(records)
        validated_df = InquiryTimelineSchema.validate(df)

        storage = LakehouseStorageWriter(root_dir="data/lakehouse")
        write_res = storage.write_dataset_partitioned(
            df=validated_df,
            layer="silver",
            table_name="inquiry_timeline",
            partition_keys={
                "tenant_id": "policia_civil_sp",
                "case_id": args.case_id
            },
            mode="append"
        )
        print("\n" + "=" * 80)
        print(f" [LAKEHOUSE] {write_res['records_written']} fatos persistidos na camada Silver Parquet:")
        print(f" -> {write_res['file_path']}")
        print("=" * 80)

if __name__ == "__main__":
    main()
