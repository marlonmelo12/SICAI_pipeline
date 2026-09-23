# 02 — Contexto de Negócio e Setorial

## 1. Cenário de Mercado e Oportunidade Econômica

O setor de computação forense e o ecossistema de **LegalTech** vivenciam um crescimento expressivo no Brasil e no mundo, impulsionado pela digitalização completa dos processos judiciais (Processo Judicial Eletrônico - PJe), proliferação de crimes cibernéticos e pelo rigor crescente de compliance corporativo e regulatório [FATO DO PROJETO].

No entanto, a análise pericial de evidências digitais ainda enfrenta barreiras estruturais críticas [FATO DO PROJETO]:
* **Volume massivo de dados:** Perícias lidam rotineiramente com terabytes de discos rígidos, smartphones, logs de servidores e capturas de tráfego de rede.
* **Processos artesanais e fragmentados:** Uso de ferramentas heterogêneas sem consolidação integrada, exigindo dias ou semanas de trabalho pericial manual.
* **Vulnerabilidade probatória:** Elevado risco de contaminação da prova digital, extravio de metadados temporais ou quebra acidental da cadeia de custódia, levando à nulidade processual de provas em juízo.
* **Custo proibitivo para PMEs:** Escritórios de advocacia de médio e pequeno porte, empresas de contabilidade e consultorias enfrentam restrições orçamentárias severas para adquirir ferramentas forenses tradicionais de alto custo.

---

## 2. Proposta de Valor e Modelo SaaS

O SICAI posiciona-se como uma plataforma capaz de democratizar o acesso à perícia digital avançada através do modelo **SaaS (Software as a Service)** [FATO DO PROJETO]:
1. **Redução Drástica do Tempo de Análise:** Automação de tarefas mecânicas de cruzamento cronológico e validação de hashes.
2. **Mitigação de Nulidades Processuais:** Identificação proativa de fragilidades probatórias antes que a evidência seja contestada pela parte adversa.
3. **Escalabilidade e Receita Recorrente:** Oferta de planos modulares baseados em volume de custódia e capacidade analítica, atendendo desde peritos individuais até grandes órgãos públicos e corporações [FATO DO PROJETO].

---

## 3. Arcabouço Normativo e Regulatório Brasileiro

O SICAI possui como requisito primordial de negócio a conformidade técnico-jurídica com a legislação nacional [FATO DO PROJETO]:

### 3.1 Pacote Anticrime (Lei nº 13.964/2019) — Arts. 158-A a 158-F do CPP
O Código de Processo Penal estabelece as 10 etapas obrigatórias da cadeia de custódia [FATO DO PROJETO]:
1. **Reconhecimento:** identificação do artefato como de interesse probatório.
2. **Isolamento:** preservação do local ou do ambiente digital sem alteração do estado original.
3. **Fixação:** descrição detalhada do estado da evidência, metadados e contexto.
4. **Coleta:** apreensão e empacotamento formal.
5. **Recebimento:** transferência de posse com lavratura de termo circunstanciado.
6. **Transporte:** movimentação segura entre custodiantes.
7. **Processamento:** exame pericial propriamente dito (geração de cópias bit a bit / imagens forenses).
8. **Armazenamento:** guarda em condições seguras contra modificações físicas ou lógicas.
9. **Descarte:** destinação autorizada judicialmente após o encerramento da relevância probatória.
10. **Rastreabilidade geral:** o art. 158-E veda categoricamente a admissão de provas cuja cadeia de custódia não possa ser plenamente demonstrada.

> **Impacto na Data Platform:** Cada uma das 10 etapas acima deve ser tratada como entidade ou evento canônico no banco de metadados (`silver.custody_events`), com registro do custodiante, hash de transição e timestamp verificado.

### 3.2 Lei Geral de Proteção de Dados (LGPD — Lei nº 13.709/2018)
Evidências digitais frequentemente contêm dados pessoais sensíveis (mensagens trocadas, prontuários, registros financeiros).
* Aplicação do Princípio da Necessidade e Minimização [FATO DO PROJETO].
* Isolamento estrito entre casos e tenants para evitar vazamento cruzado [FATO DO PROJETO].
* Mecanismos de anonimização e pseudonimização para datasets utilizados em benchmarking e calibração de IA [FATO DO PROJETO].

---

## 4. Mapeamento de Riscos de Negócio e Estratégias de Mitigação

| Risco de Negócio [FATO DO PROJETO] | Descrição | Estratégia de Mitigação Técnica da Plataforma |
| :--- | :--- | :--- |
| **Resistência dos Usuários / Peritos** | Peritos desconfiarem de análises automatizadas de IA como uma "caixa-preta". | Implementação de XAI (Explicabilidade), provendo rastreabilidade linha a linha do porquê cada inconsistência foi apontada [FATO DO PROJETO]. |
| **Fragilidade Jurídica em Tribunal** | Contestação de laudos produzidos por sistema automatizado sob alegação de adulteração. | Imutabilidade WORM no object storage, conferência dupla de hashes SHA-256 e SHA-512 e linhagem ponta a ponta [RECOMENDAÇÃO]. |
| **Vazamento de Dados Sensíveis** | Acesso indevido a dados de inquéritos ou processos sob segredo de justiça. | Criptografia at-rest e in-transit, Row-Level Security (RLS) no PostgreSQL e segregação física/lógica de buckets [RECOMENDAÇÃO]. |
| **Dependência Excessiva de Especialistas** | Gargalo na validação técnica de cada feature devido à escassez de peritos. | Criação de simuladores de evidências sintéticas e suítes de testes de qualidade automatizados (Soda/Pandera) [PROPOSTA]. |
