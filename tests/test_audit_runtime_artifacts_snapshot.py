from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_audit_runtime_artifacts_snapshot_dry_run(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "audit" / "audit_runtime_artifacts_snapshot.py"

    hb = tmp_path / "health" / "watchdog.heartbeat"
    hb.parent.mkdir(parents=True, exist_ok=True)
    hb.write_text('{"ok":true}\n', encoding="utf-8")

    tele = tmp_path / "data" / "events.jsonl"
    tele.parent.mkdir(parents=True, exist_ok=True)
    tele.write_text('{"a":1}\n', encoding="utf-8")

    log = tmp_path / "logs" / "service.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("ok\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--runtime-root",
            str(tmp_path),
            "--heartbeat",
            "watchdog=health/watchdog.heartbeat",
            "--telemetry-glob",
            "data/*.jsonl",
            "--service-log-glob",
            "logs/*.log",
            "--dry-run",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["checks"]["heartbeats"][0]["name"] == "watchdog"
    assert len(payload["checks"]["telemetry"]) == 1
    assert len(payload["checks"]["service_logs"]) == 1
