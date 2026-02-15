from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import nbformat

from conftest import import_module_from_path, scripts_root


def _make_simple_notebook() -> nbformat.NotebookNode:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(
            "# a cell that uses a parameter\n"
            "result = x * 2\n"
            "print(result)\n"
        )
    ]
    return nb


def test_apply_parameters_inserts_tagged_cell() -> None:
    script_path = scripts_root() / "notebooks" / "notebook_parameter_sweep.py"
    mod = import_module_from_path("notebook_parameter_sweep", script_path)

    nb = _make_simple_notebook()
    mod.apply_parameters_to_notebook(nb, {"x": 3})

    assert nb.cells[0].cell_type == "code"
    assert "parameters" in (nb.cells[0].metadata.get("tags") or [])
    assert "x = 3" in nb.cells[0].source


def test_cli_no_execute_writes_outputs_and_report(tmp_path: Path) -> None:
    script = scripts_root() / "notebooks" / "notebook_parameter_sweep.py"

    in_nb = tmp_path / "in.ipynb"
    nbformat.write(_make_simple_notebook(), str(in_nb))

    outdir = tmp_path / "out"
    grid = tmp_path / "grid.json"
    grid.write_text(json.dumps([{"x": 1}, {"x": 2}]), encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            str(in_nb),
            "--grid",
            str(grid),
            "--outdir",
            str(outdir),
            "--no-execute",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr

    out0 = outdir / "in__run000.ipynb"
    out1 = outdir / "in__run001.ipynb"
    assert out0.exists() and out1.exists()

    report = outdir / "sweep_report.json"
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["parameters"]["x"] == 1
