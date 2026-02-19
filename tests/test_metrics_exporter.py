from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_metrics_exporter_cli_writes_csv_with_stable_header(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "metrics_exporter.py"

    in_path = tmp_path / "metrics.jsonl"
    out_path = tmp_path / "metrics.csv"

    in_path.write_text(json.dumps({"timestamp": "2025-01-01T00:00:00Z", "total_links": 3}) + "\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), str(in_path), str(out_path)],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert out_path.exists()

    with out_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)

    # A couple of key fields that must exist in the stable export
    assert header[0] == "timestamp"
    assert "total_links" in header
