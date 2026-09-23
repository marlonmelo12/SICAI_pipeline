# 07 — Catálogo de Decisões Arquiteturais (ADRs)

Este documento registra as decisões arquiteturais fundamentais da plataforma de Engenharia de Dados do SICAI, detalhando contexto, alternativas, justificativas e trade-offs assumidos.

---

### ADR-001: Armazenamento da Evidência Bruta Original
* **Status:** Proposto [PROPOSTA]
* **Contexto:** Evidências forenses digitais consistem em grandes volumes de dados não estruturados e binários (imagens de disco de 50GB a 1TB, capturas de rede, dumps de memória, arquivos de áudio/vídeo). A preservação exige garantia de imutabilidade bit a bit, auditabilidade e custo-benefício escalável.
* **Problema:** Onde e como armazenar a evidência digital bruta de forma segura, imutável e compatível com ambientes on-premises e nuvem?
* **Alternativas Analisadas:**
  1. *Banco de Dados Relacional (BLOBs no PostgreSQL):* Invidente e ineficiente; geraria gargalo severo de I/O, inflação do WAL e backups inviáveis.
  2. *Sistema de Arquivos Local (NFS / SAN):* Falta de APIs padronizadas, complexidade em garantir imutabilidade programática e dificuldade de escalabilidade multi-tenant.
  3. *Object Storage compatível com S3 (Garage / AWS S3):* Padrão industrial, suporte a políticas WORM (Object Lock), desacoplamento total de computação, streaming de bytes de alta performance.
* **Decisão:** Adotar **Object Storage compatível com protocolo S3** (Garage para ambientes on-premises e desenvolvimento local; AWS S3 ou equivalente para implantações em nuvem) [PROPOSTA].
* **Justificativa:** Atende perfeitamente ao requisito de imutabilidade, suporta armazenamento de terabytes com custo controlado e fornece APIs seguras de streaming para os workers de processamento.
* **Trade-offs:** Exige serviço de storage leve (Garage daemon) na infraestrutura local, necessitando configuração adequada de layout de metadados e blocos de dados.

---

### ADR-002: Formato de Tabela Analítica (Lakehouse)
* **Status:** Proposto [PROPOSTA]
* **Contexto:** A plataforma processará milhões de eventos forenses que precisam ser consultados analiticamente, correlacionados e submetidos a algoritmos de Machine Learning. É fundamental suportar evolução segura de esquemas e, acima de tudo, **reprodutibilidade histórica (Time Travel)** para auditoria de perícias.
* **Problema:** Qual formato de tabela aberta adotar para as camadas Silver e Gold sobre o Object Storage?
* **Alternativas Analisadas:**
  1. *Arquivos Parquet Puros (Pastas no S3):* Sem controle de transação ACID, sem time travel nativo, risco de corrupção em escritas concorrentes.
  2. *Delta Lake:* Excelente maturidade, porém fortemente associado ao ecossistema Databricks / Spark.
  3. *Apache Iceberg:* Padrão aberto governado pela Apache Software Foundation, excelente suporte a múltiplos motores (Trino, DuckDB, Spark, Flink, StarRocks), hidden partitioning e forte suporte a Time Travel via snapshots imutáveis.
* **Decisão:** Adotar **Apache Iceberg** com arquivos subjacentes em **Apache Parquet** [PROPOSTA].
* **Justificativa:** O Iceberg permite versionar os dados da mesma forma que versionamos código. Uma consulta pericial realizada hoje sobre um snapshot de seis meses atrás produzirá exatamente os mesmos dados, preenchendo o requisito de auditabilidade forense estrita.
* **Trade-offs:** Exige um serviço de Catálogo Iceberg (como Project Nessie, REST Catalog ou JDBC Catalog no PostgreSQL).

---

### ADR-003: Orquestrador de Pipelines e Fluxos de Dados
* **Status:** Proposto [PROPOSTA]
* **Contexto:** A ingestão, parsing, validação de qualidade, normalização e cálculo de features exigem agendamento ordenado, retentativas automáticas, dependências de dados e monitoramento visual.
* **Problema:** Qual ferramenta adotar para orquestração batch de ponta a ponta?
* **Alternativas Analisadas:**
  1. *Scripts Cron / Triggers Customizados:* Impossível de auditar, sem linhagem, sem interface de retry ou tratamento de falhas.
  2. *Dagster / Prefect:* Excelentes ferramentas modernas, porém com menor ubiquidade em infraestruturas legadas de órgãos públicos.
  3. *Apache Airflow:* O orquestrador open-source mais consolidado do mercado, com suporte a TaskFlow API, dynamic task mapping, Airflow Datasets (data-aware scheduling) e vasta comunidade.
* **Decisão:** Adotar **Apache Airflow** como orquestrador central de pipelines batch [PROPOSTA].
* **Justificativa:** Estabilidade, riqueza de operadores e capacidade comprovada de coordenar fluxos complexos de ETL/ELT com auditoria e reexecuções idempotentes.
* **Trade-offs:** Pegada de memória e dependência de componentes como Scheduler, Webserver e Metadata DB.

---

### ADR-004: Event Streaming e Desacoplamento Assíncrono
* **Status:** Proposto [PROPOSTA]
* **Contexto:** A submissão de evidências pesadas para parsing não pode bloquear a aplicação web. Além disso, eventos de auditoria e status de processamento devem ser transmitidos em tempo real para os módulos de IA e dashboards.
* **Problema:** Qual mecanismo de mensageria adotar para comunicação orientada a eventos?
* **Alternativas Analisadas:**
  1. *RabbitMQ:* Excelente para filas de tarefas simples, mas sem retenção distribuída e replay de log com a mesma robustez do Kafka.
  2. *Redis Pub/Sub:* Volátil e não persistente por padrão.
  3. *Apache Kafka / Redpanda:* Plataforma líder de event streaming distribuído, com persistência durável em disco, capacidade de replay de tópicos e particionamento horizontal.
* **Decisão:** Adotar **Apache Kafka** (ou Redpanda em cenários de baixo overhead de infraestrutura) para o barramento de eventos operacionais [PROPOSTA].
* **Justificativa:** Permite que parsers e serviços de IA consumam eventos em seu próprio ritmo, suporta Dead Letter Queues (DLQ) nativamente e possibilita replay histórico de eventos.
* **Trade-offs:** Complexidade operacional se mal dimensionado. Manter tópicos focados estritamente em eventos de notificação e audit log, jamais trafegando arquivos binários de evidência no payload.

---

### ADR-005: Banco Relacional Operacional e Metadados (OLTP)
* **Status:** Proposto [PROPOSTA]
* **Contexto:** O produto SICAI necessita de um repositório centralizado de alta integridade para gerenciar tenants, usuários, casos, cadeias de custódia formalizadas, permissões e status de execução.
* **Problema:** Qual banco transacional utilizar?
* **Alternativas Analisadas:**
  1. *MongoDB:* Flexível, mas com menor garantia de integridade referencial relacional estrita exigida pelo modelo formal da cadeia de custódia.
  2. *PostgreSQL:* Padrão ouro em bancos relacionais open-source, suporte a tipos avançados (UUID, JSONB, arrays), extensões robustas (pgcrypto) e suporte a **Row-Level Security (RLS)** nativo para arquitetura multi-tenant SaaS.
* **Decisão:** Adotar **PostgreSQL** para a camada OLTP e catálogo de metadados operacionais [PROPOSTA].
* **Justificativa:** Confiabilidade ACID insuperável, suporte nativo a RLS garantindo que um cliente SaaS jamais veja dados de outro tenant, e excelente integração com Airflow e Iceberg JDBC Catalog.
* **Trade-offs:** Deve ser protegido rigorosamente para não receber o volume de dados analíticos (que deve ir para o Iceberg).

---

### ADR-006: Camada de Busca e Serving Pericial
* **Status:** Proposto [PROPOSTA]
* **Contexto:** Peritos necessitam realizar buscas rápidas de palavras-chave, hashes, IPs, nomes de arquivos e artefatos extraídos em milhões de linhas de logs de múltiplos sistemas.
* **Problema:** Como viabilizar consultas interativas de alta velocidade sobre texto e metadados forenses?
* **Alternativas Analisadas:**
  1. *Consultas SQL LIKE / ILIKE no PostgreSQL:* Inviáveis para dezenas de milhões de registros.
  2. *OpenSearch:* Fork open-source comunitário do Elasticsearch mantido pela Linux Foundation / AWS, livre de restrições de licença comercial, com suporte maduro a full-text search, filtros facetados e index lifecycle management (ILM).
* **Decisão:** Adotar **OpenSearch** como motor de busca e serving pericial [PROPOSTA].
* **Justificativa:** Fornece tempo de resposta em milissegundos para buscas textuais e timeline exploration, operando como camada de indexação derivada (sem ser a fonte da verdade).
* **Trade-offs:** Demanda consumo de memória RAM para caches e gestão de índices/shards.
