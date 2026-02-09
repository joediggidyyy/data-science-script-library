from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_transform_text_replaces_common_symbols() -> None:
    mod = import_module_from_path(
        "clean_unicode",
        scripts_root() / "docs" / "text" / "clean_unicode.py",
    )

    out, changed = mod.transform_text("Hello \u201cworld\u201d \u2192 test\u2026")
    assert changed >= 1
    assert '"world"' in out
    assert "->" in out
    assert "..." in out


def test_cli_inplace_creates_backup_and_modifies_file(tmp_path: Path) -> None:
    script = scripts_root() / "docs" / "text" / "clean_unicode.py"

    p = tmp_path / "sample.md"
    p.write_text("A \u201ctest\u201d \u2192 ok\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), str(p), "--ext", ".md", "--inplace"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0

    backup = p.with_suffix(p.suffix + ".bak")
    assert backup.exists()

    new_text = p.read_text(encoding="utf-8")
    assert "\u201c" not in new_text
    assert "->" in new_text
