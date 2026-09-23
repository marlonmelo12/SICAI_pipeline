# 05 — Catálogo Formal de Requisitos da Plataforma de Dados

## 1. Requisitos Funcionais (RF-DATA)

| ID | Nome do Requisito | Descrição Detalhada | Fase / MVP | Prioridade |
| :--- | :--- | :--- | :--- | :--- |
| **RF-DATA-001** | Ingestão de fontes heterogêneas | Capacidade de ingerir evidências digitais em múltiplos formatos: imagens de disco (E01, RAW/DD), arquivos de log (Syslog, EVTX, Apache), extrações forenses de mensageiros e capturas de rede (PCAP) [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-002** | Preservação da evidência original | Armazenar o payload original em área de isolamento WORM (Write Once, Read Many), impedindo qualquer alteração ou deleção física/lógica [FATO DO PROJETO]. | MVP 1 | Crítica |
| **RF-DATA-003** | Identificação única de ingestões | Gerar UUIDv4 imutável para cada processo de ingestão (`ingestion_id`), associando-o ao caso (`case_id`), evidência (`evidence_id`) e tenant (`tenant_id`) [FATO DO PROJETO]. | MVP 1 | Crítica |
| **RF-DATA-004** | Verificação criptográfica de integridade | Calcular automaticamente hashes SHA-256 e SHA-512 no momento exato da ingestão e validar bit a bit com o hash declarado pelo custodiante [FATO DO PROJETO]. | MVP 1 | Crítica |
| **RF-DATA-005** | Extração de metadados | Extrair e catalogar metadados técnicos de origem: tamanho em bytes, MIME type, timestamps do sistema de arquivos (MACB - Modified, Accessed, Changed, Born) e cabeçalhos de custódia [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-006** | Parsing especializado forense | Executar workers conteinerizados e isolados utilizando ferramentas consolidadas (TSK, Plaso, parsers específicos) para decodificação segura de artefatos [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-007** | Normalização para modelo canônico | Mapear os dados heterogêneos extraídos para o Esquema Canônico Forense SICAI (tabelas Iceberg Silver) [FATO DO PROJETO]. | MVP 1 | Crítica |
| **RF-DATA-008** | Data Quality automatizada | Aplicar suítes de validação de qualidade automáticas (Soda Core / Pandera) cobrindo completude, unicidade, validade temporal e integridade relacional [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-009** | Data Lineage e proveniência | Rastrear a genealogia de cada registro analítico ou finding, permitindo reconstituição reversa até a evidência bruta e versão do parser [FATO DO PROJETO]. | MVP 2 | Crítica |
| **RF-DATA-010** | Versionamento de schemas | Versionar explicitamente os contratos e esquemas de dados (ex: `ForensicEvent v1.0`, `v1.1`, `v2.0`), rejeitando schema drift silencioso [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-011** | Versionamento de datasets | Gerenciar snapshots de tabelas analíticas via Apache Iceberg, possibilitando reproduzir laudos periciais com base no estado exato dos dados em data pregressa (Time Travel) [FATO DO PROJETO]. | MVP 2 | Alta |
| **RF-DATA-012** | Reprocessamento não-destrutivo | Permitir a reexecução de parsers atualizados sobre a evidência bruta original sem sobrescrever nem corromper resultados históricos [FATO DO PROJETO]. | MVP 2 | Crítica |
| **RF-DATA-013** | Idempotência operacional | Assegurar que submissões duplicadas da mesma evidência ou mensagem não criem registros espúrios ou duplicidades no Lakehouse [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-014** | Tratamento tolerante a falhas | Garantir que o pipeline capture exceções e preserve o estado da execução sem travar o processamento das demais evidências [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-015** | Dead Letter Queue (DLQ) | Encaminhar payloads ou logs corrompidos/incompatíveis para filas de quarentena (DLQ) acompanhados de diagnósticos para auditoria pericial [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-016** | Disponibilização para Analytics | Expor tabelas consolidadas (Camada Gold) para consumo dos dashboards periciais de rastreabilidade e consistência temporal [FATO DO PROJETO]. | MVP 1 | Alta |
| **RF-DATA-017** | Disponibilização para ML/AI | Fornecer feature datasets estruturados, normalizados e anonimizados para treinamento e inferência dos modelos de detecção de anomalias e XAI [FATO DO PROJETO]. | MVP 2 | Alta |
| **RF-DATA-018** | Busca e serving pericial | Indexar eventos e metadados no OpenSearch para permitir busca textual facetada e exploração interativa de evidências por peritos [FATO DO PROJETO]. | MVP 1 | Média |
| **RF-DATA-019** | Auditoria das operações de dados | Registrar trilha de auditoria imutável (append-only) contendo quem acessou, consultou, exportou ou executou transformações sobre os dados [FATO DO PROJETO]. | MVP 3 | Crítica |
| **RF-DATA-020** | Observabilidade dos pipelines | Emitir métricas operacionais (taxa de sucesso, latência p95/p99, throughput, lag do Kafka) via OpenTelemetry [FATO DO PROJETO]. | MVP 2 | Média |

---

## 2. Requisitos Não Funcionais (RNF-DATA)

| ID | Nome do Requisito | Critério de Aceitação / Parâmetro Técnico | Prioridade |
| :--- | :--- | :--- | :--- |
| **RNF-DATA-001**| Escalabilidade horizontal | Arquitetura desacoplada onde workers de parsing, nós de computação e brokers de streaming escalam horizontalmente e independentemente [FATO DO PROJETO]. | Crítica |
| **RNF-DATA-002**| Alta reprodutibilidade | Garantia de que reprocessar a evidência original com a mesma versão de parser e pipeline produzirá rigorosamente o mesmo dataset final [FATO DO PROJETO]. | Crítica |
| **RNF-DATA-003**| Idempotência estrita | Pipeline garante consistência e deduplicação estrutural por chave canônica e hash criptográfico [FATO DO PROJETO]. | Alta |
| **RNF-DATA-004**| Auditabilidade nativa | Todo registro gerado na plataforma possui carimbo de tempo auditável e identificador de execução associado [FATO DO PROJETO]. | Crítica |
| **RNF-DATA-005**| Rastreabilidade ponta a ponta | Capacidade técnica de navegar reversamente: Finding → Modelo → Feature → Evento Silver → Artefato Bronze → Hash Original [FATO DO PROJETO]. | Crítica |
| **RNF-DATA-006**| Versionamento formal | Versionamento rigoroso de código, DAGs, schemas, modelos e datasets (Apache Iceberg Snapshots) [FATO DO PROJETO]. | Alta |
| **RNF-DATA-007**| Tolerância a falhas | Mecanismos automáticos de retry com exponential backoff e fallback para DLQ em casos de pane [FATO DO PROJETO]. | Alta |
| **RNF-DATA-008**| Observabilidade distribuída | Instrumentação de traces, métricas e logs estruturados em conformidade com o padrão OpenTelemetry [FATO DO PROJETO]. | Média |
| **RNF-DATA-009**| Segurança da informação | Criptografia em repouso (AES-256) e em trânsito (TLS 1.3), princípio do menor privilégio e segregação de chaves criptográficas [FATO DO PROJETO]. | Crítica |
| **RNF-DATA-010**| Isolamento entre tenants | Garantia de isolamento multi-tenant lógico (RLS no PostgreSQL e políticas de prefixo/bucket no S3) e possibilidade de segregação física [FATO DO PROJETO]. | Crítica |
| **RNF-DATA-011**| Portabilidade e Vendor Neutral | Ausência de acoplamento com provedores específicos de nuvem (compatibilidade total on-premises e multi-cloud) [FATO DO PROJETO]. | Alta |
| **RNF-DATA-012**| Open-source first | Priorização absoluta de bibliotecas, bancos e frameworks open-source consolidados e ativamente mantidos [FATO DO PROJETO]. | Crítica |
| **RNF-DATA-013**| Interoperabilidade | Disponibilização de interfaces abertas (APIs REST, exportação Parquet/JSON, OpenLineage) para integração com ecossistema forense [FATO DO PROJETO]. | Alta |
| **RNF-DATA-014**| Evolução de schema segura | Suporte a inclusão e depreciação de campos sem corromper consultas de consumidores legados [FATO DO PROJETO]. | Alta |
| **RNF-DATA-015**| Reprocessamento não-destrutivo | Preservação perene e intocável do dado bruto em caso de reprocessamento por evolução de regra de negócio [FATO DO PROJETO]. | Crítica |
