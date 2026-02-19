from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_audit_repo_health_snapshot_dry_run_flags_tracked_logs(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "audit_repo_health_snapshot.py"

    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True, text=True)
    bad = tmp_path / "logs" / "app.log"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True, text=True)

    res = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--dry-run"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    flagged = payload["checks"]["tracked_should_not_be_tracked"]
    assert any("logs/app.log" in p.replace("\\", "/") for p in flagged)
