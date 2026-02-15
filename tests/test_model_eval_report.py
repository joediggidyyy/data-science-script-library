from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import import_module_from_path, scripts_root


def test_evaluate_regression_basic() -> None:
    mod = import_module_from_path(
        "model_eval_report",
        scripts_root() / "ml" / "model_eval_report.py",
    )

    y_true = ["1.0", "2.0", "3.0"]
    y_pred = ["1.0", "2.5", "2.5"]

    metrics = mod.evaluate_regression(y_true, y_pred)
    assert metrics["n"] == 3
    assert metrics["mse"] >= 0


def test_evaluate_classification_basic() -> None:
    mod = import_module_from_path(
        "model_eval_report_cls",
        scripts_root() / "ml" / "model_eval_report.py",
    )

    y_true = ["A", "A", "B", "B"]
    y_pred = ["A", "B", "B", "B"]

    metrics = mod.evaluate_classification(y_true, y_pred)
    assert metrics["n"] == 4
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert "confusion_matrix" in metrics


def test_cli_writes_reports(tmp_path: Path) -> None:
    script = scripts_root() / "ml" / "model_eval_report.py"

    y_true = tmp_path / "y_true.csv"
    y_pred = tmp_path / "y_pred.csv"
    out_dir = tmp_path / "out"

    y_true.write_text("y\nA\nA\nB\nB\n", encoding="utf-8")
    y_pred.write_text("y\nA\nB\nB\nB\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--task",
            "classification",
            "--y-true",
            str(y_true),
            "--y-pred",
            str(y_pred),
            "--out",
            str(out_dir),
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr

    assert (out_dir / "model_eval.json").exists()
    assert (out_dir / "model_eval.md").exists()

    payload = json.loads((out_dir / "model_eval.json").read_text(encoding="utf-8"))
    assert payload["task"] == "classification"
    assert "accuracy" in payload["metrics"]
