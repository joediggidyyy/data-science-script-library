from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_check_pidfiles_status_reports_running_process(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "check_pidfiles_status.py"
    pidfile = tmp_path / "self.pid"
    pidfile.write_text(str(os.getpid()) + "\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--pidfile",
            f"self={pidfile}",
            "--json",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    rows = payload["results"]
    assert len(rows) == 1
    assert rows[0]["running"] is True
