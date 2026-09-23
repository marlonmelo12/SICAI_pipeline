-- dbt/models/marts/fct_case_unified_timeline.sql
-- Reconstrução cronológica unificada de todos os eventos da cadeia de custódia e arquivos extraídos

WITH custody_events AS (
    SELECT
        event_id,
        tenant_id,
        case_id,
        evidence_id,
        'CUSTODY_EVENT' AS record_source,
        stage AS event_type,
        event_timestamp,
        actor_name AS actor,
        seal_number AS artifact_ref,
        notes AS details
    FROM {{ ref('stg_custody_events') }}
),
artifact_events AS (
    SELECT
        artifact_id AS event_id,
        tenant_id,
        case_id,
        evidence_id,
        'FORENSIC_ARTIFACT' AS record_source,
        'FILE_MODIFICATION' AS event_type,
        modified_at AS event_timestamp,
        'DEVICE_OS' AS actor,
        file_path AS artifact_ref,
        CONCAT('File size: ', size_bytes, ' bytes | SHA256: ', COALESCE(sha256, 'N/A')) AS details
    FROM {{ ref('stg_forensic_artifacts') }}
    WHERE modified_at IS NOT NULL
)
SELECT * FROM custody_events
UNION ALL
SELECT * FROM artifact_events
ORDER BY event_timestamp ASC
