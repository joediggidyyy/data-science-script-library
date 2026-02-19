from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import scripts_root


def test_generate_script_inventory_outputs_json_and_markdown(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "inventory" / "generate_script_inventory.py"

    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir(parents=True, exist_ok=True)

    (src / "tool.py").write_text("print('ok')\n", encoding="utf-8")
    (src / "helper.ps1").write_text("Write-Host 'ok'\n", encoding="utf-8")
    (src / "notes.txt").write_text("ignore me\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), "--root", str(src), "--out", str(out)],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr

    json_path = out / "script_inventory.json"
    md_path = out / "script_inventory.md"
    assert json_path.exists()
    assert md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total"] == 2
