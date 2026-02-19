from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_audit_status_drift_detects_mismatch(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "audit_status_drift.py"

    tasks = tmp_path / "tasks.json"
    task_doc = tmp_path / "jobs" / "JOB_1.md"
    task_doc.parent.mkdir(parents=True, exist_ok=True)
    task_doc.write_text("**Status**: open\n", encoding="utf-8")
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "JOB-1",
                    "path": "jobs/JOB_1.md",
                    "status": "completed",
                }
            ]
        ),
        encoding="utf-8",
    )

    dash = tmp_path / "dashboard.md"
    dash.write_text("| id | a | b | c | d | status |\n|---|---|---|---|---|---|\n| JOB-1 | | | | | open |\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--tasks-json",
            str(tasks),
            "--dashboard-md",
            str(dash),
            "--repo-root",
            str(tmp_path),
            "--dry-run",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["checked_task_count"] == 1
    assert len(payload["violations"]) >= 1
