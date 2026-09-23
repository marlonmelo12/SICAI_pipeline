# tests/unit/test_crypto.py
import pytest
import tempfile
import os
from src.common.crypto import compute_hashes_streaming, verify_hash

def test_streaming_hash_calculation():
    test_data = b"SICAI_FORENSIC_INTEGRITY_TEST_DATA_2026"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(test_data)
        tmp_path = tmp.name

    try:
        hashes = compute_hashes_streaming(tmp_path)
        assert "sha256" in hashes
        assert "sha512" in hashes
        assert "md5" in hashes
        assert len(hashes["sha256"]) == 64
        assert len(hashes["sha512"]) == 128
        assert len(hashes["md5"]) == 32

        # Verifica consistência
        assert verify_hash(tmp_path, hashes["sha256"], "sha256") is True
        assert verify_hash(tmp_path, "0000000000000000000000000000000000000000000000000000000000000000", "sha256") is False
    finally:
        os.remove(tmp_path)
