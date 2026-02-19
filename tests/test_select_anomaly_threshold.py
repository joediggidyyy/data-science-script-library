from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_cli_writes_threshold_report_and_json(tmp_path: Path) -> None:
    script = scripts_root() / "ml" / "select_anomaly_threshold.py"

    scores_csv = tmp_path / "scores.csv"
    out_report = tmp_path / "threshold_report.md"

    scores_csv.write_text(
        "record_id,score_raw\n"
        "a,0.1\n"
        "b,0.2\n"
        "c,0.5\n"
        "d,0.9\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--scores",
            str(scores_csv),
            "--target-fpr",
            "0.25",
            "--out-report",
            str(out_report),
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert out_report.exists()

    json_path = out_report.with_suffix(".json")
    assert json_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["n_samples"] == 4
    assert 0.0 <= payload["actual_fpr"] <= 1.0
