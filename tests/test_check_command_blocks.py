from __future__ import annotations

import re
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_scan_file_flags_plaintext_commands_outside_fences(tmp_path: Path) -> None:
    mod = import_module_from_path(
        "check_command_blocks",
        scripts_root() / "docs" / "markdown" / "check_command_blocks.py",
    )

    md = tmp_path / "README.md"
    md.write_text(
        "\n".join(
            [
                "# Title",
                "This is prose.",
                "python -m pip install thing",  # violation
                "",
                "```bash",
                "python -m pip install ok",  # inside fence; ok
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    cmd_re = re.compile(r"^\s*(python|pip)\b", re.IGNORECASE)
    violations = mod.scan_file(md, cmd_re)

    assert any("python -m pip install thing" in v[1] for v in violations)
    assert not any("install ok" in v[1] for v in violations)


def test_scan_file_ignores_headings(tmp_path: Path) -> None:
    mod = import_module_from_path(
        "check_command_blocks_headings",
        scripts_root() / "docs" / "markdown" / "check_command_blocks.py",
    )

    md = tmp_path / "doc.md"
    md.write_text("# python is great\n", encoding="utf-8")

    cmd_re = re.compile(r"^\s*(python)\b", re.IGNORECASE)
    assert mod.scan_file(md, cmd_re) == []
