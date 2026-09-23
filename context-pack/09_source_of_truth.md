# 09 — Fonte da Verdade e Hierarquia Probatória

## 1. Documento Primário do Projeto

A fonte primária formal e irrevogável para escopo, objetivos, cronograma, riscos e entregas do projeto é [FATO DO PROJETO]:

> **`PT_MM_Forense_v3.docx.pdf`**  
> *Plano de Trabalho — parte integrante do Acordo de Parceria para Pesquisa, Desenvolvimento e Inovação (PD&I) entre UFC, Unidade EMBRAPII LESC/UFC, Marcos Ja de Bm Ciências Forenses e FASTEF/SICAFI.*

### Regra de Precedência Hermenêutica:
Em caso de aparente discrepância ou conflito entre:
* Sugestões arquiteturais de mercado;
* Práticas genéricas de engenharia de software;
* Recomendações geradas por modelos de IA;
* **O conteúdo do Plano de Trabalho (`PT_MM_Forense_v3.docx.pdf`);**

**Prevalecerá sempre e de forma absoluta o conteúdo do Plano de Trabalho formal do projeto.** [FATO DO PROJETO]

---

## 2. Hierarquia da Verdade Probatória no Sistema

Para assegurar validade jurídica incontestável e aderência aos arts. 158-A a 158-F do CPP, a plataforma de dados institui a seguinte **Hierarquia de Confiabilidade da Informação**:

```text
       [GRAU MÁXIMO DE VERDADE]
                 ▲
                 │   NÍVEL 1: EVIDÊNCIA BRUTA ORIGINAL (WORM / HASH INTACTO)
                 │   - Bit a bit inalterado, preservado no Object Storage.
                 │
                 │   NÍVEL 2: METADADOS CANÔNICOS & MANIFESTS DE INGESTÃO
                 │   - Hashes SHA-256/512, termos de apreensão assinados, timestamps de custódia.
                 │
                 │   NÍVEL 3: EVENTOS & ARTEFATOS NORMALIZADOS (SILVER)
                 │   - Dados extraídos por parsers determinísticos e auditados.
                 │
                 │   NÍVEL 4: TIMELINES & FEATURE DATASETS (GOLD)
                 │   - Projeções analíticas consolidadas por pipelines e dbt.
                 │
                 │   NÍVEL 5: FINDINGS & APONTAMENTOS DE IA
                 │   - Alertas probabilísticos de inconsistências e scores de risco.
                 │
                 │   NÍVEL 6: DECISÃO TÉCNICO-JURÍDICA HUMANA
                 ▼   - Conclusão do perito judicial ou assistente técnico.
       [INTERPRETAÇÃO E JULGAMENTO]
```

---

## 3. Axiomas de Integridade Probatória

1. **Axioma da Não-Mutabilidade da Prova:**
   - Nenhum modelo de IA, rotina de ETL, trigger de banco de dados ou usuário administrador tem permissão para alterar os bytes de uma evidência bruta após a sua ingestão [FATO DO PROJETO].
2. **Axioma da Derivação Auditável:**
   - Qualquer informação presente na camada Silver ou Gold deve possuir caminho determinístico e auditável que demonstre de qual evidência e de qual trecho de código ela foi originada [FATO DO PROJETO].
3. **Axioma da Separação entre Dado e Inferência:**
   - O sistema nunca deve confundir a constatação fática de um dado forense com a inferência estatística de um modelo de Machine Learning [RECOMENDAÇÃO].
   - **`AI Output ≠ Evidence`** [RECOMENDAÇÃO]
   - **`AI Finding ≠ Human Conclusion`** [RECOMENDAÇÃO]
