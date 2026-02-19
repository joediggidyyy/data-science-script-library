from __future__ import annotations

from pathlib import Path

import pytest

from conftest import import_module_from_path, scripts_root


def test_convert_to_pdf_creates_file(tmp_path: Path) -> None:
    pytest.importorskip("reportlab")

    script = scripts_root() / "docs" / "convert_to_pdf.py"
    mod = import_module_from_path("convert_to_pdf_mod", script)

    md_path = tmp_path / "input.md"
    pdf_path = tmp_path / "output.pdf"
    md_path.write_text("# Hello\n\n- item one\n- item two\n", encoding="utf-8")

    mod.convert_md_to_pdf(str(md_path), str(pdf_path))

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
