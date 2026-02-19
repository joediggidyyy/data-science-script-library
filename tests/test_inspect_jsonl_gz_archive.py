from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_cli_inspects_jsonl_gz_archive(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "inspect_jsonl_gz_archive.py"
    in_gz = tmp_path / "sample.jsonl.gz"

    rows = [
        {"a": 1, "b": "x"},
        {"a": 2, "c": True},
    ]
    with gzip.open(in_gz, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    res = subprocess.run(
        [sys.executable, str(script), str(in_gz), "--top", "10", "--sample", "1"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert "Total Records: 2" in res.stdout
    assert "Key Frequency" in res.stdout
