# 00 — Contexto Geral do Projeto SICAI

## 1. Identificação do Projeto e Parcerias Institucionais

O **SICAI — Sistema Inteligente de Cadeia de Custódia com Inteligência Artificial** é um projeto de Pesquisa, Desenvolvimento e Inovação (PD&I) estruturado no modelo de cooperação tecnológica e cofinanciamento tripartite [FATO DO PROJETO]:

* **Instituição de Ensino e Pesquisa / Gestão Técnica:** Universidade Federal do Ceará (**UFC**).
* **Unidade Credenciada EMBRAPII:** **Unidade EMBRAPII LESC/UFC** em Sistemas Embarcados Complexos, responsável pelo aporte de recursos financeiros da EMBRAPII e suporte de infraestrutura laboratorial e de P&D [FATO DO PROJETO].
* **Empresa Parceira / Demandante Tecnológico:** **MARCOS JA DE BM CIENCIAS FORENSES**, responsável pelo direcionamento pericial, levantamento de requisitos de negócio e inserção mercadológica da solução [FATO DO PROJETO].
* **Fundação Interveniente de Apoio Administrativo/Financeiro:** Fundação de Apoio a Serviços Técnicos, Ensino e Fomento a Pesquisas (**FASTEF / SICAFI**) [FATO DO PROJETO].

---

## 2. Propósito Fundamental

O propósito do SICAI é transformar a gestão e a auditoria da cadeia de custódia de evidências digitais através da automatização de processos periciais, garantindo [FATO DO PROJETO]:
1. **Integridade estrita:** preservação matemática e criptográfica da evidência desde a sua apreensão até o desfecho processual.
2. **Rastreabilidade ininterrupta:** registro transparente e auditável de cada agente, evento e operação que manipulou o artefato.
3. **Consistência temporal:** detecção de quebras cronológicas, retroações ou incoerências em logs temporais.
4. **Confiabilidade probatória:** elevação do padrão de certeza jurídica para subsidiar peritos, advogados, órgãos públicos e magistrados.

---

## 3. Princípio Fundamental de Arquitetura de Dados

> **A evidência original é imutável. Tudo que o sistema produzir a partir dela é derivado, versionado e rastreável.** [FATO DO PROJETO]

Fluxo axiológico da informação no SICAI:
```text
                    EVIDÊNCIA BRUTA
                           │
                 [IMUTABILIDADE WORM]
                           │
                           ▼
                 DATA PLATFORM (SICAI)
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    Metadados          Artefatos           Eventos
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                   Timeline Unificada
                           │
                           ▼
                    Feature Dataset
                           │
                           ▼
                   Modelos de ML / IA
                           │
                           ▼
                        Finding
                           │
                           ▼
                 Revisão Humana / Perito
```

* **A IA não é fonte primária da verdade.** A IA gera análises probabilísticas e apontamentos (`findings`), os quais jamais alteram a evidência subjacente e sempre dependem de validação humana qualificada.
* **Separabilidade Estrita:**
  - `AI Output ≠ Evidence` [RECOMENDAÇÃO]
  - `AI Finding ≠ Human Conclusion` [RECOMENDAÇÃO]

---

## 4. Fronteiras Arquiteturais da Engenharia de Dados

A equipe de Engenharia de Dados é o alicerce operacional da plataforma e tem como fronteira clara:

```text
Fontes (Discos, Logs, PCAPs, APIs)
  ↓
Ingestão Confiável & Validação Hash
  ↓
Armazenamento Bruto (Bronze / WORM)
  ↓
Parsing Seguro & Extração Isolada
  ↓
Normalização Canônica (Silver)
  ↓
Data Quality Automatizada
  ↓
Data Lineage & Proveniência
  ↓
Data Governance & Versionamento
  ↓
Datasets Analíticos & Serving (Gold)
  ↓
[Fronteira]: Analytics / Modelos de IA / Aplicações Web
```

### O que está DENTRO do domínio de Engenharia de Dados:
* Arquitetura e operação do Lakehouse (Garage/S3 + Iceberg + Parquet) [PROPOSTA].
* Pipelines batch e streaming (Airflow e Kafka) com garantia de idempotência e tolerância a falhas [PROPOSTA].
* Modelagem do Esquema Canônico Forense [PROPOSTA].
* Enforcement de Data Contracts, Schema Registry e Data Quality (Soda, Pandera, GX) [RECOMENDAÇÃO].
* Rastreabilidade e linhagem reversa ponta a ponta (OpenLineage) [RECOMENDAÇÃO].
* Camada de busca e serving analítico (OpenSearch, PostgreSQL para metadados) [PROPOSTA].

### O que está FORA do domínio de Engenharia de Dados (Fronteira Arquitetural):
* Interfaces gráficas finais de usuário (Frontend/UX/Next.js) [FATO DO PROJETO].
* Regras de negócio procedimentais do backend aplicacional (gestão de faturas, checkout SaaS, etc.) [FATO DO PROJETO].
* Algoritmos proprietários de Machine Learning e calibração de modelos estatísticos (domínio de Data Science/IA) [FATO DO PROJETO].
* Formulação de teses jurídicas ou validação pericial formal dos laudos (domínio do especialista humano/Marcos Ja de Bm) [FATO DO PROJETO].
