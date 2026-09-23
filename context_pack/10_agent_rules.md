# 10 — Regras de Atuação dos Agentes e Engenheiros (Agent Rules)

Este documento estabelece o código de conduta técnica e metodológica para engenheiros de software, arquitetos de dados e agentes autônomos de IA atuando no desenvolvimento da plataforma SICAI.

---

## 1. Princípio Fundamental de Engenharia de Software e Dados

> **Simples onde pode ser simples, sofisticada onde precisa ser sofisticada, escalável onde houver necessidade, auditável por natureza, baseada em padrões abertos, reutilizando tecnologias consolidadas e sem reinventar componentes já resolvidos pela indústria.**

### Hierarquia de Prioridades Inegociável:
Em qualquer situação de conflito entre requisitos ou escolhas técnicas, adote a seguinte ordem de prevalência:
```text
Correção
   >
Auditabilidade
   >
Confiabilidade
   >
Simplicidade
   >
Manutenibilidade
   >
Escalabilidade
   >
Performance
```

---

## 2. Taxonomia Obrigatória de Classificação de Informações

Para evitar **alucinações arquiteturais**, qualquer documento, especificação, comentário de código ou resposta técnica DEVE classificar suas afirmações utilizando rigorosamente as seguintes tags:

* **`[FATO DO PROJETO]`**: Informação explicitamente documentada no Plano de Trabalho (`PT_MM_Forense_v3.docx.pdf`) ou no Acordo de Parceria formal.
* **`[DECISÃO EXISTENTE]`**: Decisão arquitetural ou de engenharia já deliberada e formalmente aprovada pela liderança do projeto.
* **`[PROPOSTA]`**: Solução técnica ou desenho arquitetural sugerido pela equipe para resolução de um problema.
* **`[RECOMENDAÇÃO]`**: Boa prática consagrada de engenharia de dados/software sugerida pelo arquiteto.
* **`[HIPÓTESE]`**: Suposição operacional ou técnica adotada provisoriamente para permitir o avanço do trabalho.
* **`[PONTO EM ABERTO]`**: Lacuna de informação técnica, de negócio ou jurídica ainda não definida.
* **`[VALIDAÇÃO NECESSÁRIA]`**: Item que exige confirmação formal de perito forense, operador do direito ou liderança institucional.

> **Regra Absoluta:** Nunca transforme uma recomendação técnica ou hipótese em requisito já aprovado sem a devida deliberação.

---

## 3. Catálogo de Anti-Padrões Proibidos

É expressamente proibido adotar ou tolerar os seguintes anti-padrões no ecossistema de dados do SICAI:

1. **Microserviços por Moda:** Não decompor a aplicação em dezenas de microsserviços sem justificativa concreta de isolamento de ciclo de vida, performance ou segurança. Priorize uma aplicação modular com workers especializados desacoplados [RECOMENDAÇÃO].
2. **Banco Único para Tudo (Golden Hammer):** Não utilizar o PostgreSQL como Data Lake para milhões de logs, nem tentar usar o OpenSearch como banco relacional transacional [RECOMENDAÇÃO].
3. **Kafka como Data Lake Permanente:** Não utilizar tópicos do Kafka como local de guarda perene de evidências [FATO DO PROJETO].
4. **PostgreSQL como Repositório de Arquivos:** Proibido armazenar arquivos binários de evidência em colunas `BYTEA` ou `BLOB` relacionais [RECOMENDAÇÃO].
5. **IA como Fonte da Verdade:** Modelos de IA e LLMs produzem hipóteses e apontamentos (`findings`), jamais conclusões periciais imutáveis [FATO DO PROJETO].
6. **LLM para Validação de Custódia:** Não usar modelos de linguagem de caixa-preta para validar integridade criptográfica de hashes ou regras lógicas determinísticas [RECOMENDAÇÃO].
7. **Parsers Proprietários Reinventados:** Proibido criar código próprio de baixo nível para parsing de sistemas de arquivos ou formatos forenses padronizados quando ferramentas consolidadas (The Sleuth Kit, Plaso, etc.) já existirem [FATO DO PROJETO].
8. **ETL Monolítico Destrutivo:** Pipelines que executam mutações `UPDATE in-place` em dados históricos são terminantemente vedadas [RECOMENDAÇÃO].
9. **Pipelines sem Idempotência ou Lineage:** Todo job de processamento deve poder ser reexecutado sem gerar duplicatas e deve registrar seus artefatos de entrada e saída [RECOMENDAÇÃO].
10. **Silenciamento de Exceções sem DLQ:** É proibido capturar erros de parsing com blocos vazios (`catch (Exception e) {}`). Falhas devem ser auditadas e roteadas para Dead Letter Queues com metadados de diagnóstico [RECOMENDAÇÃO].

---

## 4. Método para Tomada de Decisão Tecnológica

Sempre que um engenheiro ou agente propuser a inclusão de uma nova tecnologia, biblioteca ou framework, deverá apresentar a seguinte estrutura formal:

```text
Problema Concreto a Resolver
  ↓
Requisitos e Restrições
  ↓
Alternativas Existentes Avaliadas (mínimo 2)
  ↓
Critérios de Comparação Objetivos (Licença, Maturidade, Comunidade, Operabilidade)
  ↓
Escolha Recomendada
  ↓
Trade-offs Assumidos e Custos Ocultos
```

> **A pergunta de controle:** *"Qual problema real este componente resolve que os componentes existentes na stack não resolvem adequadamente?"* Se não houver resposta inequívoca, a tecnologia NÃO deve ser adicionada.
