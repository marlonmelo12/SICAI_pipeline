# src/workers/llm_timeline_worker.py
"""
Worker Especialista de Inteligência Forense: Reconstituição Cronológica de Inquéritos
e Extração do Grafo de Atores Processuais via IA (LLM Qwen 2.5).
"""
import os
import re
import json
import uuid
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import requests

from src.quality.schemas import (
    InquiryActor,
    InquiryChronologicalEvent,
    InquiryTimelineReport,
    InquiryTimelineSchema
)

logger = logging.getLogger("SICAI.LLMTimelineWorker")

TIMELINE_SYSTEM_PROMPT = """Você é um perito em Inteligência Forense e Análise Processual Penal.
Sua missão é ler páginas de autos de inquérito policial / processos judiciais e reconstruir a LINHA DO TEMPO DOS FATOS e identificar TODOS OS ATORES (pessoas físicas) citados.

Para cada fato relevante na página:
1. Extraia a DATA REAL em que o fato ocorreu (ex: despacho, decisão, autorização de operação, busca e apreensão, depoimento, laudo).
2. Identifique TODAS AS PESSOAS citadas e qualifique seu papel:
   - DELEGADO, JUIZ, PROMOTOR, ESCRIVAO, INVESTIGADOR, PERITO, INVESTIGADO, TESTEMUNHA, VITIMA, ADVOGADO ou OUTRO.
3. Extraia uma CITAÇÃO LITERAL exata (palavra por palavra) da página que comprova o fato (Ground Truth).

Formato de Resposta (retorne APENAS um array JSON de objetos):
[
  {
    "event_date": "AAAA-MM-DD" (ou null se não for possível determinar a data exata),
    "raw_date_text": "texto literal da data como consta na página (ex: '20 de setembro de 2021')",
    "event_type": "INSTAURACAO" | "DECISAO_JUDICIAL" | "AUTORIZACAO_OPERACAO" | "MANDADO_BUSCA" | "APREENSAO" | "OITIVA_DEPOIMENTO" | "RELATORIO_INVESTIGACAO" | "LAUDO_PERICIAL" | "DESPACHO" | "OUTRO",
    "headline": "Resumo sintético em 1 frase (ex: 'Operação autorizada e mandados expedidos pelo Juiz')",
    "description": "Narrativa factual do que aconteceu, quem determinou e detalhes relevantes",
    "actors": [
      {
        "name": "Nome Completo da Pessoa",
        "role": "DELEGADO" | "JUIZ" | "PROMOTOR" | "ESCRIVAO" | "INVESTIGADOR" | "PERITO" | "INVESTIGADO" | "TESTEMUNHA" | "VITIMA" | "ADVOGADO" | "OUTRO",
        "organization": "Órgão/Lotação (ex: 'Polícia Civil - DEIC', 'TJSP', 'Ministério Público')"
      }
    ],
    "page_number": <numero_da_pagina>,
    "verbatim_quote": "Trecho literal da página que comprova essa ocorrência"
  }
]
Se a página não contiver fatos jurídicos/policiais ou pessoas físicas relevantes, retorne [].
"""

MESES_PT = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
    "abril": "04", "maio": "05", "junho": "06", "julho": "07",
    "agosto": "08", "setembro": "09", "outubro": "10", "novembro": "11",
    "dezembro": "12"
}

def parse_brazilian_date(text: str) -> Optional[str]:
    """Converte datas em português para o formato AAAA-MM-DD."""
    if not text:
        return None

    # 1. Padrão ISO YYYY-MM-DD
    iso_match = re.search(r'\b(20\d{2}|19\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b', text)
    if iso_match:
        return iso_match.group(0)

    # 2. Padrão numérico brasileiro DD/MM/AAAA ou DD.MM.AAAA
    br_num = re.search(r'\b(0?[1-9]|[12]\d|3[01])[\/\.](0?[1-9]|1[0-2])[\/\.](20\d{2}|19\d{2})\b', text)
    if br_num:
        dia, mes, ano = br_num.groups()
        return f"{ano}-{int(mes):02d}-{int(dia):02d}"

    # 3. Padrão extenso: "20 de setembro de 2021"
    ext_match = re.search(r'\b(0?[1-9]|[12]\d|3[01])\s+de\s+([a-zç]+)\s+de\s+(20\d{2}|19\d{2})\b', text.lower())
    if ext_match:
        dia, mes_nome, ano = ext_match.groups()
        if mes_nome in MESES_PT:
            return f"{ano}-{MESES_PT[mes_nome]}-{int(dia):02d}"

    return None


class TimelineEngineAdapter(ABC):
    @abstractmethod
    def extract_from_text(self, page_text: str, page_number: int) -> List[InquiryChronologicalEvent]:
        pass


class OllamaTimelineEngine(TimelineEngineAdapter):
    """Motor de inferência conectando à LLM Qwen 2.5 no Ollama com aceleração GPU."""

    def __init__(self, host: str = "http://localhost:11434", model_name: str = "qwen2.5:7b", timeout: int = 120):
        self.host = host.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def extract_from_text(self, page_text: str, page_number: int) -> List[InquiryChronologicalEvent]:
        if not page_text or len(page_text.strip()) < 30:
            return []

        user_content = (
            f"PÁGINA PROCESSUAL {page_number}:\n"
            f"\"\"\"\n{page_text}\n\"\"\"\n\n"
            f"Extraia todos os fatos da linha do tempo e atores citados nesta página em JSON."
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": TIMELINE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": 1536
            }
        }

        try:
            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            raw_content = data.get("message", {}).get("content", "[]")

            parsed = json.loads(raw_content)
            if isinstance(parsed, dict) and "events" in parsed:
                parsed = parsed["events"]
            elif isinstance(parsed, dict):
                parsed = [parsed]

            valid_events = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                item["page_number"] = page_number

                # Normalização de data se ausente ou imperfeita
                if not item.get("event_date") and item.get("raw_date_text"):
                    item["event_date"] = parse_brazilian_date(item["raw_date_text"])
                if not item.get("event_date"):
                    item["event_date"] = parse_brazilian_date(page_text)

                try:
                    event = InquiryChronologicalEvent(**item)
                    if event.verify_ground_truth(page_text):
                        valid_events.append(event)
                    else:
                        logger.warning(f"Página {page_number}: Evento descartado por Ground Truth - '{event.verbatim_quote[:50]}...'")
                except Exception as val_err:
                    logger.debug(f"Página {page_number}: Erro de validação de evento: {val_err}")

            return valid_events
        except Exception as err:
            logger.error(f"Erro na extração de timeline para página {page_number}: {err}")
            return []


class MockTimelineEngine(TimelineEngineAdapter):
    """Motor de contingência determinístico para testes e validação contínua sem GPU."""

    def extract_from_text(self, page_text: str, page_number: int) -> List[InquiryChronologicalEvent]:
        events = []
        low = page_text.lower()

        # Detecção de data
        dt = parse_brazilian_date(page_text) or "2021-09-20"

        # Padrão 1: Instauração ou Portaria
        if "portaria" in low or "instaur" in low:
            actor = InquiryActor(name="EDMAR ROGERIO DIAS CAPARROZ", role="DELEGADO", organization="Polícia Civil")
            events.append(
                InquiryChronologicalEvent(
                    event_date=dt,
                    raw_date_text="20 de setembro de 2021",
                    event_type="INSTAURACAO",
                    headline="Instauração de Inquérito Policial por Portaria",
                    description="Inquérito instaurado pelo Delegado de Polícia para apurar infrações penais.",
                    actors=[actor],
                    page_number=page_number,
                    verbatim_quote=page_text[:80].strip() if len(page_text) >= 80 else page_text.strip()
                )
            )

        # Padrão 2: Apreensão / Operação
        if "apreens" in low or "lacre" in low:
            actor = InquiryActor(name="EDMAR ROGERIO CAPARROZ", role="DELEGADO", organization="Polícia Civil")
            actor2 = InquiryActor(name="CIRO CESAR LEMOS", role="INVESTIGADO", organization="N/A")
            events.append(
                InquiryChronologicalEvent(
                    event_date=dt,
                    raw_date_text="08/12/2021",
                    event_type="APREENSAO",
                    headline="Apreensão de bens e aparelhos em cumprimento de diligência",
                    description="Apreensão formal e acondicionamento de materiais com lacre forense.",
                    actors=[actor, actor2],
                    page_number=page_number,
                    verbatim_quote=page_text[:80].strip() if len(page_text) >= 80 else page_text.strip()
                )
            )

        # Fallback genérico se nada detectado mas tem texto
        if not events and len(page_text.strip()) > 30:
            actor = InquiryActor(name="AUTORIDADE JUDICIAL / POLICIAL", role="JUIZ", organization="TJSP")
            events.append(
                InquiryChronologicalEvent(
                    event_date=dt,
                    raw_date_text=dt,
                    event_type="DESPACHO",
                    headline="Andamento processual e despachos nos autos",
                    description="Determinação de diligências e juntada de documentos.",
                    actors=[actor],
                    page_number=page_number,
                    verbatim_quote=page_text[:60].strip()
                )
            )

        return events


class LLMInquiryTimelineWorker:
    """
    Worker orquestrador de Reconstituição Cronológica e Análise de Atores.
    """

    def __init__(
        self,
        case_id: str,
        tenant_id: str = "policia_civil_sp",
        engine: Optional[TimelineEngineAdapter] = None
    ):
        self.case_id = case_id
        self.tenant_id = tenant_id
        self.engine = engine or MockTimelineEngine()

    def process_pages(
        self,
        pages_content: List[Dict[str, Any]],
        document_name: str
    ) -> InquiryTimelineReport:
        """
        Processa uma lista de páginas [{"page_number": int, "text": str}]
        retornando a linha do tempo completa ordenada.
        """
        all_events: List[InquiryChronologicalEvent] = []

        for p in pages_content:
            p_num = p["page_number"]
            p_txt = p.get("text", "")
            if not p_txt or len(p_txt.strip()) < 30:
                continue

            extracted = self.engine.extract_from_text(p_txt, page_number=p_num)
            all_events.extend(extracted)

        # Ordenação Cronológica de T_0 até T_n
        def sort_key(ev: InquiryChronologicalEvent):
            if ev.event_date:
                return (0, ev.event_date, ev.page_number)
            return (1, "9999-99-99", ev.page_number)

        sorted_events = sorted(all_events, key=sort_key)

        return InquiryTimelineReport(
            case_id=self.case_id,
            document_name=document_name,
            total_pages_analyzed=len(pages_content),
            events=sorted_events
        )

    def extract_actors_graph(self, report: InquiryTimelineReport) -> Dict[str, Dict[str, Any]]:
        """
        Consolida todos os atores citados no inquérito:
        - Nome normalizado
        - Cargos exercidos
        - Órgãos
        - Fatos nos quais esteve envolvido
        - Páginas onde aparece
        """
        actors_dict: Dict[str, Dict[str, Any]] = {}

        for ev in report.events:
            for actor in ev.actors:
                norm_name = actor.name.strip().upper()
                if not norm_name or len(norm_name) < 3:
                    continue

                if norm_name not in actors_dict:
                    actors_dict[norm_name] = {
                        "name": norm_name,
                        "roles": set(),
                        "organizations": set(),
                        "appearances_count": 0,
                        "pages": set(),
                        "dates": set(),
                        "actions": []
                    }

                entry = actors_dict[norm_name]
                entry["roles"].add(actor.role)
                if actor.organization:
                    entry["organizations"].add(actor.organization)
                entry["appearances_count"] += 1
                entry["pages"].add(ev.page_number)
                if ev.event_date:
                    entry["dates"].add(ev.event_date)
                entry["actions"].append({
                    "date": ev.event_date or ev.raw_date_text,
                    "event_type": ev.event_type,
                    "headline": ev.headline,
                    "page": ev.page_number
                })

        # Converte sets em listas ordenadas para serialização JSON
        result = {}
        for k, v in actors_dict.items():
            result[k] = {
                "name": v["name"],
                "roles": sorted(list(v["roles"])),
                "organizations": sorted(list(v["organizations"])),
                "appearances_count": v["appearances_count"],
                "pages": sorted(list(v["pages"])),
                "dates": sorted(list(v["dates"])),
                "actions": v["actions"]
            }

        return result

    def to_dataframe_records(self, report: InquiryTimelineReport, ingestion_id: str) -> List[Dict[str, Any]]:
        """Gera linhas tabulares prontas para validação Pandera e escrita no Lakehouse Silver."""
        records = []
        for ev in report.events:
            primary_actor = ev.actors[0].name if ev.actors else None
            actors_list = [{"name": a.name, "role": a.role, "organization": a.organization} for a in ev.actors]

            records.append({
                "event_id": str(uuid.uuid4()),
                "case_id": self.case_id,
                "tenant_id": self.tenant_id,
                "event_date": ev.event_date or "",
                "raw_date_text": ev.raw_date_text or "",
                "event_type": ev.event_type,
                "headline": ev.headline,
                "description": ev.description,
                "primary_actor": primary_actor or "",
                "actors_json": json.dumps(actors_list, ensure_ascii=False),
                "page_number": ev.page_number,
                "verbatim_quote": ev.verbatim_quote,
                "ingestion_id": ingestion_id
            })
        return records
