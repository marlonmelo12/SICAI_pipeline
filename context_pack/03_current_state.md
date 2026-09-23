# 03 — Diagnóstico do Estado Atual do Projeto

## 1. Maturidade Tecnológica Atual: TRL 3

O projeto encontra-se formalmente no marco inicial, posicionado em **TRL 3 (Concepção e Prova de Conceito)** [FATO DO PROJETO].

* **Fase Operacional:** Mês 1 ao Mês 4 — Módulo 1 (MVP 1) [FATO DO PROJETO].
* **Documento Diretor Disponível:** Plano de Trabalho aprovado pelas partes (`PT_MM_Forense_v3.docx.pdf`), estabelecendo escopo, responsabilidades e cronograma [FATO DO PROJETO].

---

## 2. Inventário de Recursos e Insumos Disponíveis

1. **Documentação Primária:**
   - Acordo de Parceria PD&I entre UFC, EMBRAPII LESC/UFC, Marcos Ja de Bm e FASTEF [FATO DO PROJETO].
   - Plano de Trabalho formal detalhando o cronograma físico e os objetivos dos 3 MVPs [FATO DO PROJETO].
2. **Ambiente de Desenvolvimento:**
   - Instalações físicas e recursos computacionais providos pela UFC e Unidade EMBRAPII LESC [FATO DO PROJETO].
   - Repositório de código e ambiente local de desenvolvimento inicial.
3. **Massa de Dados Inicial:**
   - **Dados Reais:** Acesso atualmente restrito devido a questões de sigilo pericial, LGPD e segredo de justiça [FATO DO PROJETO].
   - **Solução Imediata:** Construção mandatória de um **Simulador de Evidências Digitais** capaz de gerar dados sintéticos controlados contendo inconsistências e falhas programadas (MVP 1) [FATO DO PROJETO].

---

## 3. Prontidão da Infraestrutura de Engenharia de Dados

| Componente | Situação Atual | Ação Imediata da Engenharia de Dados |
| :--- | :--- | :--- |
| **Object Storage** | Não provisionado | Propor Garage para desenvolvimento local/on-premise e S3 para cloud [PROPOSTA]. |
| **Formato de Tabela Analítica**| Não definido | Validar Apache Iceberg + Parquet para versionamento e time travel [PROPOSTA]. |
| **Banco Transacional/Metadados**| Não provisionado | Estruturar PostgreSQL com esquemas relacionais para controle de casos, evidências e RLS [PROPOSTA]. |
| **Motor de Orquestração** | Não provisionado | Especificar Apache Airflow para orquestração batch de pipelines de ingestão e DQ [PROPOSTA]. |
| **Mensageria / Eventos** | Não provisionado | Avaliar Apache Kafka para desacoplamento de notificações de ingestão e audit trail [PROPOSTA]. |
| **Data Quality & Testing** | Inexistente | Adotar frameworks modulares (Soda Core, Pandera) para verificação de esquemas e hashes [RECOMENDAÇÃO]. |
| **Linhagem de Dados** | Inexistente | Integrar OpenLineage nas pipelines para registrar proveniência de ponta a ponta [RECOMENDAÇÃO]. |

---

## 4. Riscos Técnicos Imediatos no Arranque

1. **Heterogeneidade de Formatos:** Evidências podem chegar como imagens de disco (E01, RAW/DD), arquivos de log (Syslog, EVTX, Apache), extrações forenses de mensageiros ou capturas PCAP. O sistema precisa suportar ingestão genérica sem quebrar o pipeline [FATO DO PROJETO].
2. **Ausência de Baseline de Dados Reais:** Risco de criar modelos e tabelas descoladas da realidade do perito. Mitigação: ciclos iterativos semanais com os peritos da Marcos Ja de Bm para validação dos schemas gerados pelo simulador [RECOMENDAÇÃO].
3. **Tentação de Overengineering Prematuro:** Risco de subir clusters Kubernetes ou Graph Databases complexos antes de termos o primeiro pipeline de dados canônico validado. Foco inicial: simplicidade com Docker Compose e serviços modulares desacoplados [RECOMENDAÇÃO].
