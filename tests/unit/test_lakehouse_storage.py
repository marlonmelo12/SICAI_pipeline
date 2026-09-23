# tests/unit/test_lakehouse_storage.py
import pytest
import os
import shutil
import tempfile
import pandas as pd
import pyarrow as pa
from src.lakehouse.storage import LakehouseStorageWriter

def test_lakehouse_storage_writer_write_and_read():
    temp_dir = tempfile.mkdtemp(prefix="sicai_test_lakehouse_")
    try:
        writer = LakehouseStorageWriter(root_dir=temp_dir)
        df = pd.DataFrame([
            {"event_id": "ev-01", "name": "Event 1", "score": 10.5},
            {"event_id": "ev-02", "name": "Event 2", "score": 20.0},
        ])

        partition_keys = {"tenant_id": "t1", "case_id": "c1"}
        result = writer.write_dataset_partitioned(
            df=df,
            layer="silver",
            table_name="test_events",
            partition_keys=partition_keys,
            compression="zstd",
            mode="overwrite"
        )

        assert result["status"] == "COMMITTED"
        assert result["records_written"] == 2
        assert result["bytes_written"] > 0
        assert os.path.exists(result["file_path"])
        assert result["sha256"] is not None

        # Testa leitura da partição
        table = writer.read_dataset_partition("silver", "test_events", partition_keys)
        assert table.num_rows == 2
        assert table.column_names == ["event_id", "name", "score"]

        # Testa Idempotência (Sobrescrita sem duplicações)
        df_update = pd.DataFrame([
            {"event_id": "ev-03", "name": "Event 3", "score": 30.0},
        ])
        result2 = writer.write_dataset_partitioned(
            df=df_update,
            layer="silver",
            table_name="test_events",
            partition_keys=partition_keys,
            mode="overwrite"
        )
        assert result2["records_written"] == 1
        table_after = writer.read_dataset_partition("silver", "test_events", partition_keys)
        assert table_after.num_rows == 1  # Sobrescrita limpa, sem duplicação
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
