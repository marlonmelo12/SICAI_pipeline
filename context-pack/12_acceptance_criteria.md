# 12 — Critérios de Aceitação e Definição de Pronto (DoD)

Este documento estabelece as métricas quantitativas, definições formais de qualidade e critérios de aceite que regem a aprovação de qualquer artefato ou pipeline da plataforma de Engenharia de Dados do SICAI.

---

## 1. Definição Formal de "Dado Confiável"

No ecossistema forense do SICAI, **nenhum dado é considerado confiável pelo simples fato de o pipeline ter finalizado com status 0 (sucesso)** [FATO DO PROJETO].

Um dataset, tabela ou evento somente atinge o status de **"Dado Confiável"** quando satisfaz cumulativamente os 8 pilares:
```text
  Source (Origem identificada e íntegra)
+ Schema (Aderência estrita a contrato de schema versionado)
+ Quality (Aprovação em 100% dos testes críticos de Data Quality)
+ Lineage (Proveniência rastreável até a ingestão e evidência bruta)
+ Version (Identificador imutável de snapshot / versão de execução)
+ Provenance (Assinatura do parser, ferramenta e parâmetros utilizados)
+ Integrity (Conformidade criptográfica com hashes SHA-256 da fonte)
+ Processing Status (Ausência de alertas não-tratados na DLQ)
=====================================================================
= DADO CONFIÁVEL (Apto para auditoria pericial e modelos de IA)
```

---

## 2. Definição Formal de "Pipeline Confiável"

Uma pipeline de dados do SICAI só é promovida para ambiente de produção ou homologação se for comprovadamente:

1. **Reexecutável:** Capaz de ser disparada repetidas vezes sobre a mesma partição histórica sem intervenção manual.
2. **Idempotente:** O resultado de executar $N$ vezes a pipeline sobre a mesma entrada é idêntico ao de executar exatamente 1 vez ($f(f(x)) = f(x)$).
3. **Observável:** Emite métricas de duração, latência, volume de registros processados e taxa de erro compatíveis com OpenTelemetry.
4. **Auditável:** Cada execução gera um `execution_id` único registrado no banco de metadados, contendo o hash do código e parâmetros do job.
5. **Versionada:** O código do pipeline (DAG Airflow, modelo dbt, script Python) reside no repositório Git com tag/commit rastreável.
6. **Testável:** Possui cobertura de testes unitários e de integração validando casos de sucesso e cenários de anomalia.
7. **Recuperável:** Em caso de falha transitória ou crash de infraestrutura, é capaz de retomar o processamento a partir do último checkpoint seguro sem corrupção de estado.

---

## 3. Matriz Obrigatória de Testes de Engenharia de Dados

| Categoria de Teste | Alvo / Escopo | Ferramenta / Abordagem | Critério de Aceitação Mínimo |
| :--- | :--- | :--- | :--- |
| **Testes Unitários** | Funções de normalização, parsers puros e hashing criptográfico. | `pytest` | 100% de passagem; cobertura de branches de validação temporal e timezone. |
| **Testes de Integração**| Comunicação entre componentes (API Ingestão → Garage/S3 → PostgreSQL → Kafka). | `testcontainers` / Docker Compose | Operação completa de escrita e leitura de manifestos sem erros de conexão. |
| **Data Quality Tests** | Regras de completude, domínios de valores e integridade referencial nas tabelas. | `Pandera` (runtime) + `Soda Core` (pós-load) | Zero linhas com chave primária nula; zero timestamps no futuro; zero divergências de hash. |
| **Contract Tests** | Compatibilidade de esquemas em eventos e tabelas Silver. | `jsonschema` / dbt contracts (`contract: {enforced: true}`) | Nenhuma quebra de contrato em mudanças de versão; bloqueio de schema drift silencioso. |
| **End-to-End (E2E)** | Fluxo completo da evidência bruta sintética até a disponibilização no OpenSearch e Gold. | Pipeline de teste orquestrada via Airflow DAG | Reconstituição correta da timeline de 100% dos eventos injetados pelo simulador. |
| **Testes de Carga** | Throughput de ingestão e tolerância a arquivos pesados (10GB a 100GB). | Scripts de streaming multi-thread e benchmarking I/O | Estabilidade do Garage/S3 e sem esgotamento de memória (OOM) nos workers de parsing. |
| **Testes de Falha / Caos**| Interrupção súbita de broker Kafka, storage indisponível ou arquivo corrompido. | Chaos injection / injeção de arquivos truncados | Encaminhamento correto para Dead Letter Queue (DLQ) sem travamento dos nós de processamento. |

---

## 4. Checklist de Validação da Rastreabilidade Ponta a Ponta

Para que a plataforma seja considerada aprovada em seus marcos de entrega (DoD), deve ser possível executar a seguinte **Prova de Rastreabilidade Reversa**:

```text
Passo 1: Selecionar um registro arbitrário na camada de Serving/Busca (ex: OpenSearch ou gold.case_unified_timeline).
Passo 2: Recuperar o 'event_id' e o 'ingestion_id' gravados no registro.
Passo 3: Localizar a linha correspondente na tabela 'silver.forensic_events' e conferir o 'parser_version'.
Passo 4: Localizar o manifesto em 's3://sicai-bronze/.../manifest/ingestion_manifest.json'.
Passo 5: Ler a evidência bruta original em 's3://sicai-bronze/.../raw/' e recalcular o hash SHA-256.
Passo 6: Conferir se: SHA256(arquivo_bruto) == hash_declarado_no_manifesto == hash_na_tabela_silver.
```

> **Critério de Aceitação:** Se a verificação acima for bem-sucedida de forma 100% automatizada e sem inconsistências, a cadeia de custódia computacional está validada com integridade forense comprovada.
