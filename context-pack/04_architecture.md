# 04 — Arquitetura de Referência da Plataforma de Dados

## 1. Visão Geral e Princípios Arquiteturais

A plataforma de Engenharia de Dados do SICAI foi concebida sob o paradigma **Lakehouse** com desacoplamento estrito entre **armazenamento** e **computação**, garantindo escalabilidade horizontal, auditabilidade nativa e interoperabilidade com ferramentas open-source [PROPOSTA].

### Princípios Norteadores:
1. **Imutabilidade da Evidência Bruta (WORM):** O dado original nunca sofre mutação in-place [FATO DO PROJETO].
2. **Open-Source First:** Adoção de componentes maduros e padrões abertos consolidados na indústria [FATO DO PROJETO].
3. **Auditabilidade e Linhagem Nativa:** Cada transformação gera metadados de proveniência rastreáveis da ingestão ao modelo de IA [FATO DO PROJETO].
4. **Idempotência Operacional:** Reexecuções de pipelines não geram efeitos colaterais nem registros duplicados [RECOMENDAÇÃO].

---

## 2. Diagrama Arquitetural de Referência

```mermaid
flowchart TD
    subgraph SOURCES["FONTES DE EVIDÊNCIAS DIGITAIS"]
        S1["Imagens de Disco (RAW, E01, VMDK)"]
        S2["Logs de Sistema (Syslog, EVTX, Apache)"]
        S3["Extrações Mobile & Mensagens"]
        S4["Capturas de Rede (PCAP)"]
        S5["Termos de Cadeia de Custódia (PDF, XML)"]
    end

    subgraph INGESTION["CAMADA DE INGESTÃO"]
        ING1["Ingestion Gateway (FastAPI / Upload Service)"]
        ING2["Hashing Criptográfico (SHA-256 / SHA-512)"]
        ING3["Validação de Envelope & Manifest Builder"]
    end

    subgraph STORAGE_BRONZE["CAMADA BRONZE (RAW STORAGE)"]
        B1[("Garage / S3 Object Storage (Imutável WORM)")]
        B2["bronze/tenant_id/case_id/evidence_id/raw/"]
        B3["Ingestion Manifest (JSON / Metadata)"]
    end

    subgraph STREAMING["MENSAGERIA & EVENTOS"]
        K1["Apache Kafka / Redpanda"]
        K_TOPIC["Topics: evidence.ingested | evidence.parsed | dlq.parsing.failed"]
    end

    subgraph PROCESSING["CAMADA DE PROCESSAMENTO DISTRIBUÍDO"]
        W1["Workers Especializados Forenses (Docker Sandboxed)"]
        W2["Parsers: Plaso / TSK / Custom Python Parsers"]
        W3["Data Quality Gate (Pandera / Soda Core)"]
        W4["DLQ Router (Dead Letter Queue)"]
    end

    subgraph STORAGE_SILVER["CAMADA SILVER (CANONICAL LAKEHOUSE)"]
        SL1[("Apache Iceberg Tables (Parquet Format)")]
        SL2["silver.forensic_events"]
        SL3["silver.custody_events"]
        SL4["silver.forensic_artifacts"]
        SL5["silver.evidence_metadata"]
    end

    subgraph ORCHESTRATION["ORQUESTRAÇÃO & TRANSFORMAÇÃO"]
        A1["Apache Airflow (TaskFlow API / Datasets)"]
        D1["dbt Core (Staging → Intermediate → Marts)"]
    end

    subgraph STORAGE_GOLD["CAMADA GOLD (ANALYTICAL & ML MARTS)"]
        G1[("Iceberg Marts / Feature Store")]
        G2["gold.case_unified_timeline"]
        G3["gold.custody_integrity_summary"]
        G4["gold.temporal_gap_features"]
        G5["gold.anomaly_training_dataset"]
    end

    subgraph SERVING["SERVING & DISPONIBILIZAÇÃO"]
        METADB[("PostgreSQL (Metadados / Casos / RLS Multi-tenant)")]
        SEARCH[("OpenSearch (Full-Text Search / Timeline Discovery)")]
        API["FastAPI / Backend SICAI"]
        AI_SVC["Serviços de IA (Detecção de Inconsistências / XAI)"]
        APP["Aplicação Web Pericial (Next.js / Dashboards)"]
    end

    SOURCES --> INGESTION
    ING1 --> ING2 --> ING3
    ING3 --> B1
    ING3 --> K1
    K1 --> W1
    A1 -.->|Orquestra Batch| W1
    W1 --> W2 --> W3
    W3 -- Válido --> SL1
    W3 -- Inválido --> W4 --> K1
    SL1 --> D1
    A1 -.->|Orquestra Transformações| D1
    D1 --> G1
    G1 --> SEARCH
    G1 --> AI_SVC
    SL1 --> METADB
    API --> METADB
    API --> SEARCH
    API --> AI_SVC
    API --> APP
```

---

## 3. Detalhamento das Camadas do Lakehouse

### 3.1 Camada Bronze (Raw Data Vault)
* **Objetivo:** Preservar a evidência digital exatamente como recebida, com fidelidade bit a bit [FATO DO PROJETO].
* **Tecnologia:** Object Storage compatível com S3 (Garage para on-premise/desenvolvimento, AWS S3/Azure Blob para nuvem) [PROPOSTA].
* **Estrutura de Particionamento:**
  ```text
  s3://sicai-bronze/
    └── <tenant_id>/
        └── <case_id>/
            └── <evidence_id>/
                └── <ingestion_id>/
                    ├── raw/
                    │   └── original_payload.bin (ou .E01, .pcap, etc.)
                    ├── metadata/
                    │   └── source_envelope.json
                    └── manifest/
                        └── ingestion_manifest.json (SHA-256, SHA-512, headers)
  ```
* **Políticas de Governança:** Bloqueio de deleção e sobrescrita via Object Locking / WORM policies [RECOMENDAÇÃO].

### 3.2 Camada Silver (Modelo Canônico Normalizado)
* **Objetivo:** Estruturar, tipar, validar e unificar dados forenses heterogêneos em um esquema canônico comum [PROPOSTA].
* **Tecnologia:** **Apache Iceberg** sobre formato colunar **Apache Parquet**, com controle de snapshot e time-travel nativo [PROPOSTA].
* **Entidades Canônicas:**
  - `silver.forensic_events`: Eventos normalizados extraídos de sistemas operacionais, logs, mensagens e redes.
  - `silver.custody_events`: Ações de movimentação física e lógica da prova (as 10 etapas do CPP).
  - `silver.forensic_artifacts`: Metadados de arquivos, chaves de registro, processos e executáveis encontrados.
  - `silver.evidence_metadata`: Identificadores únicos, órgãos de apreensão, peritos responsáveis e certificados de custódia.
* **Mecanismos de Qualidade:** Todas as tabelas Silver são submetidas a validações estritas de esquema e integridade referencial via **Pandera** (em tempo de execução no worker) e **Soda Core** (pós-escrita) [RECOMENDAÇÃO].

### 3.3 Camada Gold (Marts Analíticos e Feature Store)
* **Objetivo:** Disponibilizar agregações consolidadas, reconstrução cronológica unificada e matrizes de features para consumo direto por modelos de Machine Learning e interfaces periciais [PROPOSTA].
* **Tecnologia:** Apache Iceberg / Parquet materializado via **dbt** [PROPOSTA].
* **Marts Principais:**
  - `gold.case_unified_timeline`: Linha do tempo unificada de todos os eventos forenses e de custódia de um processo criminal ou corporativo.
  - `gold.temporal_gap_features`: Indicadores de janelas de tempo sem registro de logs, atrasos anormais de custódia e quebras cronológicas.
  - `gold.anomaly_training_dataset`: Datasets rotulados e anonimizados para calibração contínua dos modelos de detecção de anomalias (TRL 4 e 5).

---

## 4. Pilha Tecnológica Selecionada e Justificativas

| Domínio | Tecnologia Selecionada [PROPOSTA] | Justificativa Técnica & Alinhamento com Skills |
| :--- | :--- | :--- |
| **Object Storage** | **Garage / S3** | Padrão da indústria S3 API, software open-source leve (Rust) ideal para auto-hospedagem (self-hosted), edge e on-premise resiliente, suporte a imutabilidade WORM e streaming de arquivos binários pesados. |
| **Table Format** | **Apache Iceberg** | Formato de tabela aberto, evolução de schema segura (in-place sem reescrever dados), suporte a Time Travel (essencial para reprodutibilidade pericial) e hidden partitioning. |
| **Formato de Arquivo** | **Apache Parquet** | Formato colunar de alta compressão (Snappy/ZSTD), ideal para leituras analíticas seletivas e projeção de colunas específicas em consultas forenses. |
| **Orquestração Batch** | **Apache Airflow** | Orquestrador open-source maduro; suporte nativo a DAGs orientadas a dados (Airflow Datasets), TaskFlow API, isolamento de operadores e agendamento robusto. |
| **Event Streaming** | **Apache Kafka** | Desacoplamento assíncrono entre a chegada da evidência, o disparo dos parsers pesados e as notificações de auditoria. |
| **Banco Relacional / OLTP**| **PostgreSQL** | Motor relacional robusto com suporte a Row-Level Security (RLS) para isolamento multi-tenant, tipos nativos JSONB e integridade referencial ACID estrita para dados de gestão pericial. |
| **Motor de Busca / Serving**| **OpenSearch** | Indexação full-text de logs, metadados forenses e artefatos textuais com capacidade de agregação facetada e busca em tempo real para dashboards periciais. |
| **Transformação Lakehouse**| **dbt Core** | Engenharia analítica modular (staging, intermediate, marts), enforcement de data contracts, testes automáticos de integridade e documentação integrada. |
| **Data Quality & Validação**| **Soda Core + Pandera**| Pandera para validação in-flight no runtime do Python Worker; Soda Core para validação declarativa de integridade referencial e detecção de anomalias temporais no Lakehouse. |
| **Data Lineage** | **OpenLineage + Marquez** | Padrão aberto para captura de metadados de execução e linhagem de dados operacional ponta a ponta. |
