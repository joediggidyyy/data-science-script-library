from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_inventory_json_to_csv_converts_records(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "inventory" / "inventory_json_to_csv.py"
    input_json = tmp_path / "inventory.json"
    output_csv = tmp_path / "inventory.csv"

    input_json.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "path": "scripts/a.py",
                        "size_bytes": 12,
                        "last_modified_utc": "2025-01-01T00:00:00+00:00",
                        "last_commit_iso": "",
                        "description": "example",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, str(script), str(input_json), str(output_csv)],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert output_csv.exists()

    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["path"] == "scripts/a.py"


def test_inventory_json_to_csv_returns_nonzero_when_input_missing(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "inventory" / "inventory_json_to_csv.py"
    output_csv = tmp_path / "inventory.csv"

    res = subprocess.run(
        [sys.executable, str(script), str(tmp_path / "missing.json"), str(output_csv)],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
    )

    assert res.returncode != 0
