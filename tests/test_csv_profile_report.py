from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_profile_csv_computes_missing_uniques_and_numeric_stats(tmp_path: Path) -> None:
    mod = import_module_from_path(
        "csv_profile_report",
        scripts_root() / "data" / "csv_profile_report.py",
    )

    p = tmp_path / "in.csv"
    p.write_text(
        "x,y,name\n"
        "1,10,Alice\n"
        ",20,Bob\n"
        "3,,Alice\n",
        encoding="utf-8",
    )

    report = mod.profile_csv(p)
    cols = report["columns"]

    assert report["summary"]["rows_profiled"] == 3

    assert cols["x"]["missing"] == 1
    assert cols["x"]["nonempty"] == 2

    assert cols["name"]["unique"] == 2

    num = cols["y"]["numeric"]
    assert num is not None
    assert num["count"] == 2
    assert num["min"] == 10.0
    assert num["max"] == 20.0


def test_csv_profile_report_cli_writes_md_and_html(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "csv_profile_report.py"

    in_path = tmp_path / "in.csv"
    out_dir = tmp_path / "out"

    in_path.write_text("a,b\n1,2\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), str(in_path), "--out", str(out_dir)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr

    assert (out_dir / "csv_profile.md").exists()
    assert (out_dir / "csv_profile.html").exists()
