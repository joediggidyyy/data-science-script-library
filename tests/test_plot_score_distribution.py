from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import scripts_root


def _ensure_plot_deps() -> None:
    missing = [
        pkg
        for pkg in ("pandas", "seaborn", "matplotlib")
        if importlib.util.find_spec(pkg) is None
    ]
    if missing:
        pytest.skip(f"missing optional plotting deps: {', '.join(missing)}")


def test_cli_writes_score_distribution_png(tmp_path: Path) -> None:
    _ensure_plot_deps()

    script = scripts_root() / "plots" / "plot_score_distribution.py"
    in_csv = tmp_path / "scores.csv"
    out_png = tmp_path / "dist.png"

    in_csv.write_text(
        "score_raw\n"
        "0.10\n"
        "0.15\n"
        "0.18\n"
        "0.50\n"
        "0.90\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, str(script), str(in_csv), str(out_png)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert out_png.exists()
    assert out_png.stat().st_size > 0
