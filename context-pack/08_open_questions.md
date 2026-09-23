# 08 — Matriz de Questões em Aberto e Pontos de Validação

Este documento cataloga lacunas de informação técnica, hipóteses arquiteturais pendentes de confirmação e decisões que dependem de interação com os parceiros institucionais e peritos do projeto.

---

## 1. Questões Técnicas e Operacionais em Aberto

### Q-001: Volumetria Média e de Pico por Ingestão
* **Status:** Ponto em aberto [PONTO EM ABERTO]
* **Impacto na Arquitetura:** Define o dimensionamento do Object Storage, particionamento do Iceberg e paralelismo dos workers de parsing.
* **Hipótese Atual:** Casos típicos variam entre 5GB e 100GB; casos de alta complexidade (apreensão de múltiplos servidores) podem ultrapassar 2TB [HIPÓTESE].
* **Ação Necessária:** Reunião técnica com a equipe pericial da Marcos Ja de Bm para levantar histórico de volumetria de casos reais [VALIDAÇÃO NECESSÁRIA].

### Q-002: Formatos Forenses Prioritários no MVP 1
* **Status:** Ponto em aberto [PONTO EM ABERTO]
* **Impacto na Arquitetura:** Determina quais parsers (TSK para E01/RAW, Plaso para EVTX/Registry, scapy para PCAP) devem ser encapsulados nos workers do MVP 1.
* **Hipótese Atual:** Priorizar imagens de disco RAW/DD, imagens forenses E01 (Expert Witness Format) e logs de sistema (Windows Event Logs - EVTX e Syslog Linux) [HIPÓTESE].
* **Ação Necessária:** Validação do escopo prioritário de tipos de evidência para os cenários simulados do MVP 1 [VALIDAÇÃO NECESSÁRIA].

### Q-003: Topologia de Implantação Prioritária (On-Premises vs Cloud SaaS)
* **Status:** Ponto em aberto [PONTO EM ABERTO]
* **Impacto na Arquitetura:** Determina se a primeira entrega deve focar em Docker Compose/Kubernetes on-premise ou infraestrutura em nuvem gerenciada.
* **Hipótese Atual:** O desenvolvimento inicial deve ser 100% conteinerizado e agnóstico (Docker Compose / Garage local), permitindo deploy tanto on-premises (órgãos policiais e perícia oficial) quanto em nuvem privada (SaaS corporativo) [HIPÓTESE].
* **Ação Necessária:** Alinhamento de estratégia com a governança da EMBRAPII LESC e Marcos Ja de Bm [VALIDAÇÃO NECESSÁRIA].

### Q-004: Modelo e Necessidade Real de Grafo de Conhecimento (Módulo 3)
* **Status:** Ponto em aberto [PONTO EM ABERTO]
* **Impacto na Arquitetura:** O plano de trabalho prevê "Grafo de Conhecimento" no MVP 3. É necessário definir se isso exige a introdução de um banco de grafos nativo dedicado (ex: Neo4j) ou se a modelagem relacional avançada com consultas recursivas/CTE no PostgreSQL e projeções em Lakehouse é suficiente.
* **Hipótese Atual:** Postergar a decisão de tecnologia de grafo para a transição do MVP 2 para o MVP 3, evitando complexidade operacional desnecessária no MVP 1 [HIPÓTESE].
* **Ação Necessária:** Mapear a profundidade dos traversals e padrões de inferência relacional exigidos pelos peritos [VALIDAÇÃO NECESSÁRIA].

---

## 2. Hipóteses Técnicas a Validar

| Hipótese | Descrição | Risco Associado | Plano de Validação |
| :--- | :--- | :--- | :--- |
| **H-001** | Parsers forenses legados (TSK/Plaso) podem rodar de forma confiável em workers Python conteinerizados sem corromper memória. | Travamento de workers por estouro de memória em imagens corrompidas. | Testes de estresse com injeção de imagens truncadas e benchmarking de cgroups. |
| **H-002** | O Apache Iceberg é suficiente para atender às consultas analíticas dos dashboards sem necessidade de duplicar tudo no PostgreSQL. | Latência de consulta analítica em dashboards interativos. | Implementação de camada de serving intermediária via OpenSearch / views materializadas. |
| **H-003** | Dados forenses sintéticos gerados pelo Simulador têm representatividade suficiente para treinar modelos de detecção de anomalias no MVP 2. | Modelos superajustados a anomalias sintéticas que falham em casos reais. | Revisão periódica de anomalias com os peritos judiciais da Marcos Ja de Bm. |
