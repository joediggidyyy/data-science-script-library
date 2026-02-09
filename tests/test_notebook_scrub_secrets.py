from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import nbformat

from conftest import import_module_from_path, scripts_root


def _make_notebook_with_secrets() -> nbformat.NotebookNode:
    openai_like = "s" + "k" + "-" + "THISISNOTAREALKEYBUTLOOKSLIKEONE0000"
    github_like = "g" + "h" + "p" + "_" + "THISISNOTAREALGITHUBTOKEN0000"
    pem_begin = "-----BEGIN " + "PRIVATE KEY-----"
    pem_end = "-----END " + "PRIVATE KEY-----"

    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell(
            "Here is an API key: " + openai_like + "\n"
            "And a private key block:\n"
            + pem_begin
            + "\nabc\n"
            + pem_end
        ),
        nbformat.v4.new_code_cell(
            "print('token " + github_like + "')",
            outputs=[
                nbformat.v4.new_output(
                    "stream",
                    name="stdout",
                    text=github_like + "\n",
                )
            ],
            execution_count=7,
        ),
    ]
    return nb


def test_scrub_notebook_node_redacts_and_clears(tmp_path: Path) -> None:
    script_path = scripts_root() / "notebooks" / "notebook_scrub_secrets.py"
    mod = import_module_from_path("notebook_scrub_secrets", script_path)

    nb = _make_notebook_with_secrets()
    scrubbed, report = mod.scrub_notebook_node(nb)

    # outputs cleared + execution count cleared
    code_cell = scrubbed.cells[1]
    assert code_cell.outputs == []
    assert code_cell.execution_count is None

    # sources redacted
    openai_prefix = "s" + "k" + "-" + "THISISNOTAREALKEY"
    github_prefix = "g" + "h" + "p" + "_" + "THISISNOTAREALGITHUBTOKEN"
    private_key_marker = "BEGIN " + "PRIVATE KEY"
    all_text = "\n".join(cell.source for cell in scrubbed.cells)
    assert openai_prefix not in all_text
    assert github_prefix not in all_text
    assert private_key_marker not in all_text
    assert "[REDACTED]" in all_text

    assert report.cells_total == 2
    assert report.replacements_total >= 2


def test_cli_writes_scrubbed_notebook_and_report(tmp_path: Path) -> None:
    script = scripts_root() / "notebooks" / "notebook_scrub_secrets.py"

    in_nb = tmp_path / "in.ipynb"
    out_nb = tmp_path / "out.ipynb"

    nbformat.write(_make_notebook_with_secrets(), str(in_nb))

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            str(in_nb),
            "--out",
            str(out_nb),
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert out_nb.exists()

    report_path = out_nb.with_suffix(".scrub_report.json")
    assert report_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["cells_total"] == 2
