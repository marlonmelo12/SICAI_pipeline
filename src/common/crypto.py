# src/common/crypto.py
"""
Módulo de Integridade Criptográfica do SICAI.
Garante o cálculo simultâneo de hashes SHA-256 e SHA-512 em streaming para evidências forenses massivas.
"""
import hashlib
from typing import Dict, BinaryIO, Union
import os

CHUNK_SIZE = 64 * 1024  # 64 KB

def compute_hashes_streaming(source: Union[str, BinaryIO], chunk_size: int = CHUNK_SIZE) -> Dict[str, str]:
    """
    Calcula simultaneamente SHA-256 e SHA-512 em um único passe de streaming.
    Suporta tanto caminho de arquivo quanto objetos de stream de bytes (BytesIO / SpooledTemporaryFile).
    """
    sha256_hash = hashlib.sha256()
    sha512_hash = hashlib.sha512()
    md5_hash = hashlib.md5()

    if isinstance(source, str):
        if not os.path.exists(source):
            raise FileNotFoundError(f"Arquivo não encontrado: {source}")
        with open(source, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)
                sha512_hash.update(chunk)
                md5_hash.update(chunk)
    else:
        # Source é um stream de arquivo
        while chunk := source.read(chunk_size):
            sha256_hash.update(chunk)
            sha512_hash.update(chunk)
            md5_hash.update(chunk)

    return {
        "sha256": sha256_hash.hexdigest(),
        "sha512": sha512_hash.hexdigest(),
        "md5": md5_hash.hexdigest(),
    }

def verify_hash(file_path: str, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verifica se o hash de um arquivo em repouso confere com o valor esperado declarado.
    """
    hashes = compute_hashes_streaming(file_path)
    calculated = hashes.get(algorithm.lower())
    if not calculated:
        raise ValueError(f"Algoritmo não suportado: {algorithm}")
    return calculated.lower() == expected_hash.strip().lower()
