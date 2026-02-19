from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_report_runtime_parameters_dry_run(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "report_runtime_parameters.py"

    marker = tmp_path / "health" / "hb.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("ok\n", encoding="utf-8")

    env = os.environ.copy()
    env["BATCH_B_SAMPLE_ENV"] = "1"

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--runtime-root",
            str(tmp_path),
            "--env-name",
            "BATCH_B_SAMPLE_ENV",
            "--check-path",
            "health/hb.txt",
            "--dry-run",
        ],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["env"]["BATCH_B_SAMPLE_ENV"] is True
    assert payload["files"][0]["exists"] is True
