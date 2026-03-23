from __future__ import annotations

import json
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_extract_single_pdf_with_fake_backend(tmp_path: Path) -> None:
    script_path = scripts_root() / "docs" / "pdf" / "extract_pdf_text.py"
    mod = import_module_from_path("extract_pdf_text", script_path)

    pdf_path = tmp_path / "paper.pdf"
    out_path = tmp_path / "paper.extracted.txt"
    pdf_path.write_bytes(b"%PDF-FAKE")

    mod._BACKENDS = (("fake", lambda path, max_pages: "alpha\nbeta"),)

    rc = mod.main(["--pdf", str(pdf_path), "--out", str(out_path), "--write-manifest"])
    assert rc == 0
    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8")
    assert "[extracted_with]=fake" in text
    assert "alpha" in text

    manifest_path = out_path.with_suffix(out_path.suffix + ".manifest.json")
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["mode"] == "single"
    assert manifest["results"][0]["ok"] is True


def test_extract_pdf_directory_writes_manifest(tmp_path: Path) -> None:
    script_path = scripts_root() / "docs" / "pdf" / "extract_pdf_text.py"
    mod = import_module_from_path("extract_pdf_text_batch", script_path)

    input_dir = tmp_path / "pdfs"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    (input_dir / "a.pdf").write_bytes(b"%PDF-A")
    (input_dir / "b.pdf").write_bytes(b"%PDF-B")

    mod._BACKENDS = (("fake", lambda path, max_pages: f"text:{path.name}"),)

    rc = mod.main([
        "--input-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--write-manifest",
    ])
    assert rc == 0

    outputs = sorted(output_dir.glob("*.extracted.txt"))
    assert len(outputs) == 2
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["mode"] == "batch"
    assert len(manifest["results"]) == 2