# src/ingestion/app.py
"""
FastAPI Ingestion Gateway para a Plataforma de Dados do SICAI.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import shutil
import tempfile
import os
import json
from src.ingestion.manifest_builder import build_ingestion_manifest

app = FastAPI(
    title="SICAI Ingestion Gateway",
    description="Gateway seguro de ingestão de evidências digitais com verificação criptográfica estrita.",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "sicai-ingestion-gateway"}

@app.post("/api/v1/cases/{case_id}/evidences/upload")
async def upload_evidence(
    case_id: str,
    tenant_id: str = Form(...),
    evidence_id: str = Form(...),
    operator: str = Form("ANALYST"),
    file: UploadFile = File(...)
):
    """
    Recebe uma evidência digital, calcula hashes criptográficos e gera o manifesto de ingestão.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        manifest = build_ingestion_manifest(
            tenant_id=tenant_id,
            case_id=case_id,
            evidence_id=evidence_id,
            file_path=tmp_path,
            operator_name=operator,
            source_envelope={"original_filename": file.filename, "content_type": file.content_type}
        )
        os.remove(tmp_path)

        return {
            "message": "Evidência recebida com integridade criptográfica verificada.",
            "manifest": manifest
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
