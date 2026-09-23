-- 02_init_metadata_catalog.sql
-- Modelagem Formal da Cadeia de Custódia (Arts. 158-A a 158-F do CPP) e Catálogo Forense

-- 1. Tabela de Eventos Administrativos da Cadeia de Custódia
CREATE TABLE IF NOT EXISTS sicai_core.custody_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sicai_core.tenants(tenant_id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES sicai_core.cases(case_id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES sicai_core.evidences(evidence_id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL, -- RECONHECIMENTO, ISOLAMENTO, FIXACAO, COLETA, RECEBIMENTO, TRANSPORTE, PROCESSAMENTO, ARMAZENAMENTO, DESCARTE
    event_timestamp TIMESTAMPTZ NOT NULL,
    actor_name VARCHAR(255) NOT NULL,
    actor_role VARCHAR(100), -- DELEGADO, INVESTIGADOR, PERITO_OFICIAL, ASSISTENTE_TECNICO
    agency VARCHAR(255) NOT NULL, -- EX: POLÍCIA CIVIL SP, INSTITUTO DE CRIMINALÍSTICA, MM FORENSE
    seal_number VARCHAR(100), -- Número do Lacre físico registrado (Ex: 0011634)
    location VARCHAR(255),
    document_reference VARCHAR(255), -- Ex: BO 31/2021, Laudo 155.263/2022
    notes TEXT,
    hash_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices de busca temporal e referencial
CREATE INDEX IF NOT EXISTS idx_custody_events_evidence ON sicai_core.custody_events(evidence_id, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_custody_events_seal ON sicai_core.custody_events(seal_number);

-- 2. Tabela de Artefatos Forenses Extraídos (Metadados MACB dos Arquivos)
CREATE TABLE IF NOT EXISTS sicai_core.forensic_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sicai_core.tenants(tenant_id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES sicai_core.evidences(evidence_id) ON DELETE CASCADE,
    ingestion_id UUID NOT NULL REFERENCES sicai_core.ingestions(ingestion_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    extension VARCHAR(50),
    size_bytes BIGINT NOT NULL,
    hash_sha256 CHAR(64),
    hash_md5 CHAR(32),
    inode VARCHAR(50),
    created_at TIMESTAMPTZ,
    modified_at TIMESTAMPTZ NOT NULL,
    accessed_at TIMESTAMPTZ,
    deleted_status VARCHAR(50) DEFAULT 'INTACT', -- INTACT, DELETED, CARVED
    is_modified_under_custody BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_evidence_mod ON sicai_core.forensic_artifacts(evidence_id, modified_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_hash ON sicai_core.forensic_artifacts(hash_sha256);

-- 3. Trilha de Auditoria Imutável (Append-Only)
CREATE TABLE IF NOT EXISTS sicai_core.audit_trail (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sicai_core.tenants(tenant_id) ON DELETE CASCADE,
    user_id UUID,
    action VARCHAR(100) NOT NULL, -- INGESTION_COMPLETED, PARSER_EXECUTED, DQ_SCAN, REPORT_GENERATED
    target_type VARCHAR(50) NOT NULL, -- EVIDENCE, CASE, ARTIFACT, FINDING
    target_id UUID NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_target ON sicai_core.audit_trail(target_type, target_id, created_at);

-- RLS
ALTER TABLE sicai_core.custody_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE sicai_core.forensic_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sicai_core.audit_trail ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_custody ON sicai_core.custody_events
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);

CREATE POLICY tenant_isolation_artifacts ON sicai_core.forensic_artifacts
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);

CREATE POLICY tenant_isolation_audit ON sicai_core.audit_trail
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);
