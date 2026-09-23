# 06 — Restrições do Sistema (Constraints)

## 1. Restrições Jurídico-Processuais e Forenses

1. **Intocabilidade Probatória (Arts. 158-A e 158-B do CPP):**
   - Sob nenhuma hipótese o sistema de dados pode alterar, truncar, sobrescrever ou limpar atributos de uma evidência digital original [FATO DO PROJETO].
   - Operações de leitura sobre o arquivo bruto original devem ocorrer exclusivamente em modo somente-leitura (`read-only`) [RECOMENDAÇÃO].
2. **Cadeia de Custódia Ininterrupta (Art. 158-E do CPP):**
   - É vedada a existência de dados forenses "órfãos". Todo evento processado deve possuir vínculo obrigatório com um custodiante (agente) e com a respectiva evidência de apreensão [FATO DO PROJETO].
3. **Conformidade com a LGPD (Lei nº 13.709/2018):**
   - Dados pessoais sensíveis presentes em evidências sob segredo de justiça devem ser segregados.
   - Rotinas de treinamento de IA não podem acessar identificadores pessoais diretamente sem antes aplicar anonimização ou pseudonimização auditável [FATO DO PROJETO].

---

## 2. Restrições Técnicas e Arquiteturais

1. **Princípio de Não-Reinvenção da Roda:**
   - É terminantemente proibido desenvolver internamente ferramentas de armazenamento, formatos de arquivo, orquestradores de fluxo ou parsers forenses de baixo nível quando existirem soluções open-source maduras e ativamente mantidas [FATO DO PROJETO].
2. **Desacoplamento entre Storage e Compute:**
   - Nenhum worker de processamento pode utilizar o disco local para armazenar datasets de forma definitiva. Todo dado intermediário e final deve residir no Object Storage (Garage/S3) ou nas tabelas Iceberg [RECOMENDAÇÃO].
3. **Isolamento de Execução de Parsers Forenses:**
   - Parsers forenses lidam com arquivos binários potencialmente maliciosos (malware, exploits de buffer overflow, arquivos corrompidos).
   - A execução de parsers como TSK ou Plaso deve ocorrer dentro de contêineres Docker isolados, com limites estritos de memória RAM (cgroup limit), CPU e sem privilégios de root (`non-root user`) [RECOMENDAÇÃO].
4. **Restrição de Uso do PostgreSQL:**
   - O PostgreSQL destina-se estritamente à camada transacional (OLTP), gestão de casos, perfis de usuários, permissões e catálogo de metadados.
   - É proibido utilizar tabelas PostgreSQL para despejo massivo de milhões de eventos de log ou payloads binários [RECOMENDAÇÃO].
5. **Restrição de Uso do Kafka:**
   - O Kafka deve atuar como barramento de mensageria transitório para desacoplamento de eventos operacionais.
   - O Kafka não deve ser utilizado como repositório permanente de armazenamento de evidências [FATO DO PROJETO].

---

## 3. Restrições Operacionais e de Ambiente

1. **Deploy Híbrido (Cloud / On-Premises):**
   - Como muitos órgãos públicos e institutos de perícia possuem restrições legais para envio de evidências à nuvem pública, a arquitetura de dados deve operar identicamente em ambiente local/on-premise (Docker Compose / Kubernetes bare-metal) e em nuvem [FATO DO PROJETO].
2. **Consumo Eficiente de Recursos:**
   - Em cenários de protótipo inicial e validação (MVP 1 / TRL 3), a plataforma deve ser capaz de rodar em um único nó de desenvolvimento para permitir testes rápidos sem exigir clusters massivos [RECOMENDAÇÃO].
