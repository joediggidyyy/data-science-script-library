from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_find_near_duplicate_functions_reports_pairs(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "analysis" / "find_near_duplicate_functions.py"

    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir(parents=True, exist_ok=True)

    (src / "a.py").write_text("def f1(x):\n    y = x + 1\n    return y\n", encoding="utf-8")
    (src / "b.py").write_text("def f2(z):\n    q = z + 2\n    return q\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), "--root", str(src), "--out", str(out), "--threshold", "0.50"],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    report = out / "near_duplicate_functions_report.json"
    assert report.exists()

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["pairs_found"] >= 1
