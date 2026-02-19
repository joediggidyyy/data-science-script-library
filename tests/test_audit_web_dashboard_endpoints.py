from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_audit_web_dashboard_endpoints_dry_run(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "audit_web_dashboard_endpoints.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--base-url",
            "http://127.0.0.1:1",
            "--endpoint",
            "/",
            "--dry-run",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert "endpoints" in payload
    assert "/" in payload["endpoints"]
