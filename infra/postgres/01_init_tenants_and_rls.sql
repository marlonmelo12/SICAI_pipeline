-- 01_init_tenants_and_rls.sql
-- Inicialização de Multi-tenancy com Row-Level Security (RLS) para o SICAI

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Esquema de Metadados
CREATE SCHEMA IF NOT EXISTS sicai_core;

-- 1. Tabela de Tenants (Órgãos Públicos, Institutos de Perícia, Escritórios de Advocacia)
CREATE TABLE IF NOT EXISTS sicai_core.tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Tabela de Usuários / Operadores
CREATE TABLE IF NOT EXISTS sicai_core.users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sicai_core.tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'ANALYST', -- ADMIN, PERITO, ASSISTENTE, AUDITOR
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Tabela de Casos / Processos Judiciais (Ex: Operação Vérnix)
CREATE TABLE IF NOT EXISTS sicai_core.cases (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sicai_core.tenants(tenant_id) ON DELETE CASCADE,
    case_number VARCHAR(100) NOT NULL, -- Ex: 1501022-64.2019.8.26.0483
    inquest_number VARCHAR(100),       -- Ex: IP 192/2019
    court_branch VARCHAR(255),         -- Ex: 3ª Vara de Presidente Venceslau/SP
    title VARCHAR(255) NOT NULL,       -- Ex: Operação Vérnix
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Tabela de Evidências Digitais Apreendidas
CREATE TABLE IF NOT EXISTS sicai_core.evidences (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sicai_core.tenants(tenant_id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES sicai_core.cases(case_id) ON DELETE CASCADE,
    evidence_type VARCHAR(100) NOT NULL, -- SMARTPHONE, DISK_IMAGE, LOG_SET, PCAP
    identifier VARCHAR(255) NOT NULL,    -- Ex: Samsung SM-J510MN Galaxy J5 Metal
    serial_number VARCHAR(100),          -- RX8HA08EX9W
    imei VARCHAR(50),                    -- 359452071463772
    seizure_date TIMESTAMPTZ,            -- Data e hora da apreensão no BO
    status VARCHAR(50) NOT NULL DEFAULT 'INGESTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Tabela de Ingestões Físicas/Lógicas no Object Storage
CREATE TABLE IF NOT EXISTS sicai_core.ingestions (
    ingestion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES sicai_core.tenants(tenant_id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES sicai_core.evidences(evidence_id) ON DELETE CASCADE,
    source_filename VARCHAR(255) NOT NULL,
    storage_uri VARCHAR(1024) NOT NULL, -- s3://sicai-bronze/...
    hash_sha256 CHAR(64) NOT NULL,
    hash_sha512 CHAR(128) NOT NULL,
    size_bytes BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'STORED', -- STORED, PROCESSING, VALIDATED, FAILED
    manifest_uri VARCHAR(1024) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- ==========================================================

ALTER TABLE sicai_core.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE sicai_core.evidences ENABLE ROW LEVEL SECURITY;
ALTER TABLE sicai_core.ingestions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_cases ON sicai_core.cases
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);

CREATE POLICY tenant_isolation_evidences ON sicai_core.evidences
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);

CREATE POLICY tenant_isolation_ingestions ON sicai_core.ingestions
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);
