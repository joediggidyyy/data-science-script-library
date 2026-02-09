from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_cli_writes_png(tmp_path: Path) -> None:
    script = scripts_root() / "plots" / "plot_timeseries_from_csv.py"

    in_csv = tmp_path / "in.csv"
    out_png = tmp_path / "plot.png"

    in_csv.write_text(
        "timestamp,value\n"
        "2025-01-01,1\n"
        "2025-01-02,2\n"
        "2025-01-03,3\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            str(in_csv),
            "--out",
            str(out_png),
            "--x",
            "timestamp",
            "--y",
            "value",
            "--title",
            "Test Plot",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert out_png.exists()
    assert out_png.stat().st_size > 0
