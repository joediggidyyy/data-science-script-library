from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_validate_jsonl_records_strict_unknown_and_forbidden(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "validate_jsonl_records.py"
    data = tmp_path / "sample.jsonl"
    data.write_text(
        '{"record_id":"a1","score":0.1}\n'
        '{"record_id":"a2","content":"raw payload"}\n'
        '{"record_id":"a3","score":0.2,"extra":"x"}\n',
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            str(data),
            "--allowed-keys",
            "record_id,score",
            "--strict-unknown-keys",
            "--json",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 2
    payload = json.loads(res.stdout)
    assert payload["summary"]["error_lines"] >= 2
    assert payload["summary"]["forbidden_key_hits"] >= 1
