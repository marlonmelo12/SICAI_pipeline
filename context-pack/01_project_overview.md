# 01 — Visão Geral do Projeto SICAI

## 1. Resumo Executivo e Enquadramento Tecnológico

O **SICAI (Sistema Inteligente de Cadeia de Custódia com IA)** é um projeto com ciclo total de execução previsto de **12 meses**, estruturado para promover a progressão de maturidade tecnológica de **TRL 3 (Concepção e Prova de Conceito)** até **TRL 5 (Validação em Ambiente Relevante/Operacional)** [FATO DO PROJETO].

* **Título Público:** SICAI (Sistema Inteligente de Cadeia de Custódia com IA) [FATO DO PROJETO].
* **Resumo Público:** Solução inovadora para auditoria e validação de evidências digitais utilizando inteligência artificial para garantir integridade, rastreabilidade e confiabilidade da prova. Permite identificar inconsistências na cadeia de custódia de forma automatizada, reduzindo riscos jurídicos e aumentando a eficiência de análises periciais com aplicação nos setores jurídico, público e corporativo [FATO DO PROJETO].

---

## 2. Objetivos do Projeto

### 2.1 Objetivo Geral [FATO DO PROJETO]
Desenvolver e validar o SICAI como uma solução tecnológica inovadora capaz de automatizar a análise, validação e monitoramento da cadeia de custódia de evidências digitais, assegurando integridade, rastreabilidade, consistência temporal e confiabilidade probatória por meio da integração de técnicas avançadas de inteligência artificial e computação forense, com geração de relatórios auditáveis e suporte à tomada de decisão técnico-jurídica, visando aplicação prática em ambientes reais e escalabilidade para diferentes setores institucionais e empresariais.

### 2.2 Objetivos Específicos [FATO DO PROJETO]
1. **Modelo Computacional Estruturado:** Desenvolver representação formal da cadeia de custódia contemplando eventos, agentes/atores, evidências, metadados e relações temporais.
2. **IA para Inconsistências:** Projetar e implementar algoritmos para detecção automatizada de inconsistências, lacunas e anomalias na cadeia de custódia.
3. **Reconstrução Cronológica:** Implementar módulos inteligentes para unificação e ordenação temporal de eventos a partir de múltiplas fontes heterogêneas.
4. **Classificação de Riscos:** Criar sistema de scoring e classificação de riscos associados à confiabilidade das evidências com base em critérios técnicos e jurídico-processuais.
5. **Arquitetura Escalável de Dados:** Desenvolver infraestrutura de alto desempenho para processamento distribuído de grandes volumes de dados digitais forenses.
6. **Interface Pericial e Jurídica:** Implementar interface web intuitiva voltada a peritos, assistentes técnicos, advogados e instituições.
7. **Relatórios Auditáveis:** Gerar laudos e relatórios estruturados, rastreáveis e aptos a instruir processos judiciais e corporativos.
8. **Validação Controlada:** Validar o sistema em cenários simulados e reais utilizando bases de dados forenses representativas.
9. **Métricas Quantitativas de Desempenho:** Avaliar acurácia na detecção de falhas, redução no tempo de análise e ganho de confiabilidade comparado a processos manuais.
10. **Modelo de Negócio e Expansão:** Estruturar estratégia de produto em formato SaaS direcionada aos mercados jurídico, pericial e corporativo.
11. **Aderência Regulatória:** Garantir conformidade estrita com os arts. 158-A a 158-F do Código de Processo Penal brasileiro (Lei 13.964/2019) e com a LGPD (Lei 13.709/2018).

---

## 3. Entregas Incrementais dos Módulos (MVPs)

O projeto está dividido em três módulos consecutivos de 4 meses cada [FATO DO PROJETO]:

```text
Mês:  1    2    3    4    5    6    7    8    9    10   11   12
      ├───────────────────┼───────────────────┼───────────────────┤
      │      MVP 1        │      MVP 2        │      MVP 3        │
      │  (TRL 3 → POC)    │  (TRL 4 → Proto)  │  (TRL 5 → Real)   │
```

### MVP 1 — Modelagem, Simulação e Integração (Meses 1 a 4) [FATO DO PROJETO]
* **Foco:** Modelagem da cadeia de custódia, ingestão de dados heterogêneos, simulador de evidências com anomalias controladas, pipelines ETL/ELT iniciais e dashboards básicos de rastreabilidade.
* **Entrega:** Protótipo funcional web capaz de ingerir, estruturar, armazenar com integridade criptográfica (hashes SHA-256) e visualizar evidências simuladas em cenários controlados.

### MVP 2 — Inteligência Artificial para Auditoria e Detecção (Meses 5 a 8) [FATO DO PROJETO]
* **Foco:** Incorporação de modelos de IA para detecção de quebras na cadeia de custódia, lacunas temporais, divergência de metadados, reconstrução cronológica automatizada, scoring de risco probatório e explicabilidade (XAI).
* **Entrega:** Sistema funcional com motor de auditoria inteligente, alertas automáticos e relatórios com explicabilidade visual validado em ambiente simulado avançado.

### MVP 3 — Governança Avançada e Validação em Ambiente Real (Meses 9 a 12) [FATO DO PROJETO]
* **Foco:** Integração com dados reais/anonimizados de parceiros institucionais, trilhas de auditoria completas, versionamento estrito, controle de acesso, modelagem em Grafo de Conhecimento e estratégia de escalabilidade SaaS.
* **Entrega:** Sistema SICAI completo (TRL 5), validado em ambiente operacional relevante, com documentação técnica, diretrizes periciais e arquitetura pronta para mercado.

---

## 4. Cronograma Físico de Atividades da Engenharia de Dados

| Fase | Atividade [FATO DO PROJETO] | Janela de Meses | Foco de Engenharia de Dados |
| :--- | :--- | :--- | :--- |
| **MVP 1** | Modelagem da cadeia de custódia | Meses 1 a 4 | Schema Canônico de Eventos e Entidades Forenses |
| **MVP 1** | Desenvolvimento do simulador de evidências | Meses 1 a 4 | Gerador de datasets sintéticos com ruídos/anomalias |
| **MVP 1** | Arquitetura inicial do sistema | Meses 1 a 4 | Setup Lakehouse (Garage/S3 + Iceberg + PostgreSQL) |
| **MVP 1** | Pipelines ETL/ELT | Meses 2 a 5 | Ingestão, hashing, extração isolada e normalização |
| **MVP 2** | Expansão da arquitetura para IA | Meses 5 a 8 | Pipelines de geração de Feature Datasets no Gold |
| **MVP 2** | Reconstrução cronológica automatizada | Meses 5 a 8 | Algoritmos de ordenação e consolidação de timelines |
| **MVP 3** | Integração com dados reais/anonimizados | Meses 9 a 12 | Conectores de fontes externas e rotinas de anonimização |
| **MVP 3** | Trilhas auditáveis e versionamento | Meses 9 a 12 | Imutabilidade WORM, OpenLineage e auditoria de consultas |
| **MVP 3** | Construção do Grafo de Conhecimento | Meses 9 a 12 | Avaliação de projeção relacional vs graph db sob demanda |
