from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_md_to_reveal_html_splits_sections() -> None:
    script_path = scripts_root() / "docs" / "md_to_slides.py"
    mod = import_module_from_path("md_to_slides", script_path)

    md = "# Slide 1\n\nHello\n\n---\n\n# Slide 2\n\nWorld\n"
    html = mod.md_to_reveal_html(md, title="Deck", reveal_base="https://example.invalid", theme="black")

    assert "reveal.css" in html
    assert html.count("<section>") == 2
    assert "Slide 1" in html and "Slide 2" in html


def test_cli_writes_html(tmp_path: Path) -> None:
    script = scripts_root() / "docs" / "md_to_slides.py"

    in_md = tmp_path / "in.md"
    out_html = tmp_path / "out.html"
    in_md.write_text("# Title\n\n---\n\n# Next\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), str(in_md), str(out_html)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert out_html.exists()
    assert out_html.stat().st_size > 0
