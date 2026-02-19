from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import scripts_root


pytestmark = pytest.mark.skipif(importlib.util.find_spec("sklearn") is None, reason="scikit-learn not installed")


def test_run_ml_pipeline_demo_creates_scores(tmp_path: Path) -> None:
    script = scripts_root() / "ml" / "run_ml_pipeline_demo.py"
    out = tmp_path / "demo"
    res = subprocess.run(
        [sys.executable, str(script), "--out-dir", str(out), "--normal", "8", "--anomaly", "3"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert (out / "scores" / "scores.csv").exists()
