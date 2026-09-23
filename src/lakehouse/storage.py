# src/lakehouse/storage.py
"""
Módulo de Armazenamento e Persistência do Lakehouse SICAI.
Gerencia a gravação colunar em Apache Parquet com particionamento idempotente,
compressão ZSTD e garantia de integridade atômica.
"""
import os
import uuid
import tempfile
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from src.common.crypto import compute_hashes_streaming

DEFAULT_LAKEHOUSE_ROOT = os.getenv("LAKEHOUSE_ROOT_DIR", os.path.join(os.getcwd(), "data", "lakehouse"))

class LakehouseStorageWriter:
    """
    Responsável por gerenciar a materialização atômica e idempotente de datasets
    nas camadas Bronze, Silver e Gold do Lakehouse SICAI.
    """
    def __init__(self, root_dir: str = DEFAULT_LAKEHOUSE_ROOT):
        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

    def get_table_path(self, layer: str, table_name: str) -> str:
        return os.path.join(self.root_dir, layer, table_name)

    def write_dataset_partitioned(
        self,
        df: Union[pd.DataFrame, pa.Table],
        layer: str,
        table_name: str,
        partition_keys: Dict[str, str],
        compression: str = "zstd",
        mode: str = "overwrite"
    ) -> Dict[str, Any]:
        """
        Escreve um DataFrame em formato Parquet dentro da partição especificada.
        Implementa o padrão Write-Audit-Publish (WAP) com escrita atômica via arquivo temporário.

        Exemplo de caminho gerado:
        data/lakehouse/silver/forensic_artifacts/tenant_id=tenant_sp/case_id=case_vernix/evidence_id=ev_j5/part-xxxx.parquet
        """
        if isinstance(df, pd.DataFrame):
            if df.empty:
                return {
                    "records_written": 0,
                    "bytes_written": 0,
                    "partition_path": "",
                    "file_path": "",
                    "sha256": None,
                    "status": "SKIPPED_EMPTY"
                }
            table = pa.Table.from_pandas(df, preserve_index=False)
        else:
            table = df

        # Constrói o caminho da partição no padrão Hive (key=val/key=val)
        partition_segments = [f"{k}={v}" for k, v in partition_keys.items()]
        target_dir = os.path.join(self.root_dir, layer, table_name, *partition_segments)
        os.makedirs(target_dir, exist_ok=True)

        part_id = uuid.uuid4().hex[:12]
        final_filename = f"part-{part_id}.parquet"
        final_filepath = os.path.join(target_dir, final_filename)

        # Se mode == 'overwrite', remove arquivos pré-existentes na partição específica para garantir idempotência estrita
        if mode == "overwrite":
            for existing in os.listdir(target_dir):
                if existing.endswith(".parquet") or existing.endswith(".tmp"):
                    try:
                        os.remove(os.path.join(target_dir, existing))
                    except OSError:
                        pass

        # Escrita Atômica: grava primeiro em arquivo temporário no mesmo diretório
        temp_filepath = os.path.join(target_dir, f".tmp-{final_filename}")
        try:
            pq.write_table(
                table,
                temp_filepath,
                compression=compression,
                version="2.6",
                write_statistics=True
            )
            # Renomeação atômica (no POSIX e Windows NTFS no mesmo volume)
            os.replace(temp_filepath, final_filepath)
        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise IOError(f"Falha na escrita atômica de Parquet para {table_name}: {e}")

        # Coleta de métricas e integridade pós-escrita
        file_stats = os.stat(final_filepath)
        file_hashes = compute_hashes_streaming(final_filepath)

        return {
            "layer": layer,
            "table_name": table_name,
            "partition": partition_keys,
            "records_written": table.num_rows,
            "bytes_written": file_stats.st_size,
            "partition_path": target_dir,
            "file_path": final_filepath,
            "sha256": file_hashes["sha256"],
            "status": "COMMITTED"
        }

    def read_dataset_partition(
        self,
        layer: str,
        table_name: str,
        partition_keys: Dict[str, str]
    ) -> pa.Table:
        """
        Lê todos os arquivos Parquet de uma partição específica e retorna um PyArrow Table.
        """
        partition_segments = [f"{k}={v}" for k, v in partition_keys.items()]
        target_dir = os.path.join(self.root_dir, layer, table_name, *partition_segments)
        if not os.path.exists(target_dir):
            raise FileNotFoundError(f"Partição não encontrada: {target_dir}")

        parquet_files = [
            os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(".parquet")
        ]
        if not parquet_files:
            raise FileNotFoundError(f"Nenhum arquivo Parquet encontrado na partição: {target_dir}")

        tables = [pq.ParquetFile(pf).read() for pf in parquet_files]
        if len(tables) == 1:
            return tables[0]
        return pa.concat_tables(tables)
