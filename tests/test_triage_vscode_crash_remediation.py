from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_dry_run_with_explicit_inputs(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "triage_vscode_crash_remediation.py"

    crash_json = tmp_path / "vscode_crash_audit_test.json"
    crash_json.write_text(
        json.dumps(
            {
                "signals": {
                    "listener_leak": 12,
                    "extension_unresponsive": 1,
                    "uri_error": 0,
                    "polling_failed": 0,
                    "channel_closed": 0,
                    "dispose_error": 0,
                    "crash_or_fatal": 0,
                }
            }
        ),
        encoding="utf-8",
    )

    attr_dir = tmp_path / "attr"
    attr_dir.mkdir(parents=True, exist_ok=True)
    (attr_dir / "vscode_process_attribution_20260219_000000.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "Name": "Code.exe",
                        "PID": 1234,
                        "WS_MB": 1200,
                        "Cmd": "...ms-python.vscode-pylance...",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--dry-run",
            "--crash-evidence",
            str(crash_json),
            "--attribution-dir",
            str(attr_dir),
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert "pylance_memory_pressure: True" in res.stdout
