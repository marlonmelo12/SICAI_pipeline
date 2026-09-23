# tests/unit/test_ufdr_parser.py
import pytest
import os
from src.workers.ufdr_parser_worker import UFDRStreamingParser

UFDR_PATH = r"C:\Users\marlo\Downloads\SICAI\Vernix\DADO BRUTO\Samsung SM-J510MN Galaxy J5 Metal.ufdr"

def test_ufdr_device_metadata_extraction():
    if not os.path.exists(UFDR_PATH):
        pytest.skip("Arquivo UFDR de teste não encontrado no ambiente local")

    parser = UFDRStreamingParser(UFDR_PATH)
    meta = parser.extract_device_metadata()

    assert meta["model_number"] == "SM-J510MN"
    assert meta["vendor"].lower() == "samsung"
    assert meta["imei"] == "359452071463772"
    assert meta["android_id"] == "543545a859876ddc"
    assert meta["pa_version"] == "7.74.0.12"
    print("\n[TEST PASS] Metadados do Smartphone Samsung J5 extraídos com sucesso:", meta)

def test_ufdr_streaming_tagged_files_iteration():
    if not os.path.exists(UFDR_PATH):
        pytest.skip("Arquivo UFDR de teste não encontrado no ambiente local")

    parser = UFDRStreamingParser(UFDR_PATH)
    files_iterator = parser.iterate_tagged_files()

    sample_files = []
    for _ in range(50):
        try:
            item = next(files_iterator)
            sample_files.append(item)
        except StopIteration:
            break

    assert len(sample_files) == 50
    first = sample_files[0]
    assert "artifact_id" in first
    assert "file_path" in first
    assert "size_bytes" in first
    assert "modified_at" in first
    print(f"\n[TEST PASS] 50 arquivos extraídos em streaming sem carregar os 7.5GB em RAM: {first['file_name']}")
