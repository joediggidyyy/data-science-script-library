from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import import_module_from_path, scripts_root


def test_cli_help_works_without_pyarrow() -> None:
    script = scripts_root() / "data" / "parquet_inspect.py"
    res = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "Inspect a Parquet file" in res.stdout


def test_cli_missing_file_errors(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "parquet_inspect.py"
    missing = tmp_path / "missing.parquet"

    res = subprocess.run(
        [sys.executable, str(script), str(missing)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode != 0
    assert "file not found" in (res.stderr or "").lower()


def test_inspect_parquet_json_when_pyarrow_available(tmp_path: Path) -> None:
    pyarrow = pytest.importorskip("pyarrow")

    script_path = scripts_root() / "data" / "parquet_inspect.py"
    mod = import_module_from_path("parquet_inspect", script_path)

    # Build a tiny parquet file.
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore

    table = pa.table({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    pq_path = tmp_path / "t.parquet"
    pq.write_table(table, str(pq_path))

    summary = mod.inspect_parquet(pq_path)
    assert summary.num_rows == 3
    assert summary.num_columns == 2
    assert "a" in summary.columns and "b" in summary.columns
