# 11 — Backlog e Plano de Tarefas Imediatas da Engenharia de Dados

Este documento define o plano tático acionável da equipe de Engenharia de Dados, concentrando-se nas entregas mandatórias do **MVP 1 (Meses 1 a 4)** do projeto SICAI [FATO DO PROJETO].

---

## 1. Épico MVP 1 — Modelagem, Simulação e Integração de Dados

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        BACKLOG OPERACIONAL MVP 1                       │
├──────────────────────────┬─────────────────────────────────────────────┤
│ Sprint 1 (Meses 1-2)     │ - Setup da Infraestrutura Local (Lakehouse) │
│                          │ - Modelagem Formal do Esquema Canônico      │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Sprint 2 (Meses 2-3)     │ - Especificação do Simulador de Evidências  │
│                          │ - Pipeline de Ingestão e Hashing Cripto     │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Sprint 3 (Meses 3-4)     │ - Worker Sandboxed de Parsing e Validação   │
│                          │ - Data Quality Gates & Dashboards Iniciais  │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

## 2. Detalhamento das Tarefas de Engenharia de Dados

### Tarefa DATA-01: Scaffolding da Infraestrutura Local de Dados
* **Objetivo:** Subir ambiente conteinerizado via Docker Compose contendo os serviços essenciais da Data Platform.
* **Componentes:**
  - Garage (Object Storage compatível com S3) configurado com bucket `sicai-bronze` e `sicai-lakehouse`.
  - PostgreSQL 16 (Banco transacional OLTP e Catálogo de Metadados) com schema de multi-tenancy.
  - Apache Airflow 2.x com LocalExecutor e suporte à TaskFlow API.
  - OpenSearch 2.x e OpenSearch Dashboards para serving e consultas rápidas.
* **Critério de Conclusão:** Ambiente inicializando via `docker compose up -d` com healthchecks validados e scripts de inicialização de buckets e bancos executados com sucesso.

### Tarefa DATA-02: Modelagem Formal do Esquema Canônico Forense
* **Objetivo:** Definir os schemas de dados para a camada Silver, unificando evidências heterogêneas em estruturas relacionais analíticas previsíveis.
* **Estrutura Mínima Requerida:**
  - `silver.forensic_events`:
    - `event_id` (UUID, PK)
    - `tenant_id` (UUID, FK)
    - `case_id` (UUID, FK)
    - `evidence_id` (UUID, FK)
    - `event_type` (Enum: `FILE_ACCESS`, `PROCESS_START`, `NETWORK_CONN`, `REGISTRY_MOD`, `CUSTODY_TRANSFER`, etc.)
    - `event_timestamp` (TIMESTAMPTZ em UTC)
    - `timestamp_precision` (Enum: `MILLISECOND`, `SECOND`, `UNKNOWN`)
    - `actor` (JSONB: usuário, processo, custodiante)
    - `artifact` (JSONB: caminho, nome do arquivo, PID, hash)
    - `source_tool` (String: e.g., `plaso-2024.1`, `tsk-4.12`)
    - `ingestion_id` (UUID, rastreabilidade reversa)
    - `raw_hash_sha256` (String de 64 caracteres)
* **Critério de Conclusão:** Esquemas formalizados em DDL Iceberg/SQL, validados com a equipe pericial da Marcos Ja de Bm.

### Tarefa DATA-03: Desenvolvimento do Simulador de Evidências Digitais
* **Objetivo:** Construir gerador de dados forenses sintéticos para suprir a indisponibilidade inicial de dados reais sob sigilo judicial [FATO DO PROJETO].
* **Cenários a Simular:**
  1. *Fluxo Válido e Consistente:* Cadeia de custódia ininterrupta de 5 transferências com hashes idênticos e timestamps crescentes.
  2. *Anomalia de Integridade:* Evidência cujo hash SHA-256 no armazenamento diverge do hash lavrado no termo de recebimento.
  3. *Anomalia Temporal (Salto no Tempo):* Registro de log anterior ao timestamp de criação da partição ou posterior ao isolamento.
  4. *Anomalia de Custódia (Agente Órfão):* Evento registrado sem custodiante cadastrado na tabela de atores.
* **Critério de Conclusão:** Script Python automatizado capaz de injetar centenas de arquivos de logs e relatórios simulados no bucket Bronze, gerando ground-truth documentado.

### Tarefa DATA-04: Pipeline de Ingestão e Verificação Criptográfica
* **Objetivo:** Construir o serviço de recepção de evidências e orquestração inicial via Airflow.
* **Fluxo:**
  1. Recepção do arquivo via API / dropzone.
  2. Cálculo concorrente de hash SHA-256 e SHA-512.
  3. Persistência no Garage/S3 no padrão `s3://sicai-bronze/<tenant_id>/<case_id>/<evidence_id>/raw/`.
  4. Geração e gravação do `ingestion_manifest.json`.
  5. Registro do evento no PostgreSQL (`cases`, `evidence`, `custody_events`).
  6. Emissão de mensagem no tópico Kafka `evidence.ingested`.
* **Critério de Conclusão:** Testes automatizados cobrindo uploads com verificação positiva e rejeição de uploads corrompidos.

### Tarefa DATA-05: Implementação de Data Quality Gates com Pandera e Soda
* **Objetivo:** Integrar validações automáticas de qualidade para certificar tabelas Silver antes da disponibilização para Analytics.
* **Critério de Conclusão:** Suíte de testes Soda Core rodando pós-ingestão, reprovando automaticamente dados fora de conformidade e gerando alertas no dashboard.
