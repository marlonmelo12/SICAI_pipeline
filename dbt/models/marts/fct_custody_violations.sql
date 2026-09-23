-- dbt/models/marts/fct_custody_violations.sql
-- Detecção Automatizada de Modificações Indevidas no Estado da Coisa (Arts. 158-C/158-E do CPP)
-- Identifica os arquivos criados ou modificados após a apreensão oficial do aparelho

WITH seizure_milestone AS (
    SELECT
        evidence_id,
        MIN(event_timestamp) AS seizure_timestamp
    FROM {{ ref('stg_custody_events') }}
    WHERE stage = 'COLETA'
    GROUP BY evidence_id
),
official_exam_milestone AS (
    SELECT
        evidence_id,
        MAX(event_timestamp) AS exam_signed_timestamp
    FROM {{ ref('stg_custody_events') }}
    WHERE stage = 'PROCESSAMENTO'
    GROUP BY evidence_id
)
SELECT
    a.artifact_id,
    a.tenant_id,
    a.case_id,
    a.evidence_id,
    a.file_path,
    a.file_name,
    a.size_bytes,
    a.sha256,
    a.modified_at,
    s.seizure_timestamp,
    e.exam_signed_timestamp,
    'WRITE_ACTIVITY_UNDER_STATE_CUSTODY' AS violation_type,
    'CRITICAL' AS risk_level,
    'Arquivo sofreu modificação de escrita enquanto o aparelho se encontrava apreendido sob custódia estatal exclusiva.' AS legal_implication
FROM {{ ref('stg_forensic_artifacts') }} a
JOIN seizure_milestone s ON a.evidence_id = s.evidence_id
LEFT JOIN official_exam_milestone e ON a.evidence_id = e.evidence_id
WHERE a.modified_at > s.seizure_timestamp
  AND (e.exam_signed_timestamp IS NULL OR a.modified_at <= e.exam_signed_timestamp + INTERVAL '1 day')
