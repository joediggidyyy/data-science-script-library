from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_clean_csv_normalize_trim_drop(tmp_path: Path) -> None:
    script_path = scripts_root() / "data" / "data_cleaning_recipes.py"
    mod = import_module_from_path("data_cleaning_recipes", script_path)

    in_csv = tmp_path / "in.csv"
    out_csv = tmp_path / "out.csv"

    in_csv.write_text(
        "First Name,Score\n"
        " Alice , 10 \n"
        "  ,   \n"
        "Alice,10\n"
        "Bob, 5\n",
        encoding="utf-8",
    )

    report = mod.clean_csv(
        in_csv,
        out_csv,
        normalize_columns=True,
        trim_whitespace=True,
        drop_empty_rows=True,
        drop_duplicate_rows=True,
    )

    assert report.rows_in == 4
    assert report.rows_out == 2
    assert report.columns_out == ["first_name", "score"]

    rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8", newline="")))
    assert rows == [
        {"first_name": "Alice", "score": "10"},
        {"first_name": "Bob", "score": "5"},
    ]


def test_cli_writes_output_and_report(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "data_cleaning_recipes.py"

    in_csv = tmp_path / "in.csv"
    out_csv = tmp_path / "out.csv"

    in_csv.write_text("A B,Val\n  x , 1 \n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            str(in_csv),
            "--out",
            str(out_csv),
            "--normalize-columns",
            "--trim-whitespace",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert out_csv.exists()

    report = out_csv.with_suffix(".clean_report.json")
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["rows_out"] == 1
