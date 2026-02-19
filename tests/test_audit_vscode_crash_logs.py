from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_dry_run_parses_synthetic_vscode_logs(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "audit_vscode_crash_logs.py"

    appdata = tmp_path / "AppData"
    session = appdata / "Code" / "logs" / "20260219T000000"
    window1 = session / "window1"
    exthost = window1 / "exthost"
    exthost.mkdir(parents=True, exist_ok=True)

    (window1 / "renderer.log").write_text(
        "2026-02-19 [error] potential listener LEAK detected\n"
        "2026-02-19 [error] Polling failed: Error: Polling failed\n",
        encoding="utf-8",
    )
    (exthost / "exthost.log").write_text(
        "2026-02-19 Extension host (LocalProcess pid: 1) is unresponsive.\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["APPDATA"] = str(appdata)

    res = subprocess.run(
        [sys.executable, str(script), "--dry-run"],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert "listener_leak" in res.stdout
    assert "extension_unresponsive" in res.stdout
