from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_build_feature_dataset_outputs_manifest_and_csvs(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "build_feature_dataset.py"
    inp = tmp_path / "input.jsonl"
    out = tmp_path / "out"
    inp.write_text(
        '{"record_id":"r1","type":"post","content_length":10,"f_toxicity":0,"tv_id":"TV-0"}\n'
        '{"record_id":"r2","type":"dm","content_length":20,"f_toxicity":1,"tv_id":"TV-3"}\n',
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, str(script), "--input", str(inp), "--out-dir", str(out)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    manifest = out / "dataset_manifest.json"
    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["total_records"] == 2
    assert (out / "features.csv").exists()
    assert (out / "splits.csv").exists()
