from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_evaluate_scores_report_labeled(tmp_path: Path) -> None:
    script = scripts_root() / "ml" / "evaluate_scores_report.py"
    scores = tmp_path / "scores.csv"
    labels = tmp_path / "labels.csv"
    out_dir = tmp_path / "out"

    scores.write_text(
        "record_id,score\n"
        "a,0.9\n"
        "b,0.8\n"
        "c,0.2\n"
        "d,0.1\n",
        encoding="utf-8",
    )
    labels.write_text(
        "record_id,label\n"
        "a,1\n"
        "b,1\n"
        "c,0\n"
        "d,0\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--scores-csv",
            str(scores),
            "--labels-csv",
            str(labels),
            "--out-dir",
            str(out_dir),
            "--max-fpr",
            "0.25",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads((out_dir / "score_eval_report.json").read_text(encoding="utf-8"))
    assert payload["result"]["has_labels"] is True
    assert "f1" in payload["result"]["metrics"]


def test_evaluate_scores_report_unlabeled(tmp_path: Path) -> None:
    script = scripts_root() / "ml" / "evaluate_scores_report.py"
    scores = tmp_path / "scores.csv"
    out_dir = tmp_path / "out2"
    scores.write_text("record_id,score\na,0.9\nb,0.1\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--scores-csv",
            str(scores),
            "--out-dir",
            str(out_dir),
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads((out_dir / "score_eval_report.json").read_text(encoding="utf-8"))
    assert payload["result"]["has_labels"] is False
    assert "flag_rate" in payload["result"]["metrics"]
