from __future__ import annotations

import json
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_export_notebook_missing_file_returns_2(tmp_path: Path) -> None:
    script = scripts_root() / "notebooks" / "export_notebook.py"
    mod = import_module_from_path("export_notebook_mod", script)

    rc = mod.export_notebook(str(tmp_path / "missing.ipynb"), "html")
    assert rc == 2


def test_export_notebook_handles_optional_dependency_or_success(tmp_path: Path) -> None:
    script = scripts_root() / "notebooks" / "export_notebook.py"
    mod = import_module_from_path("export_notebook_mod_optional", script)

    notebook_path = tmp_path / "demo.ipynb"
    output_path = tmp_path / "demo.html"
    notebook_path.write_text(
        json.dumps(
            {
                "cells": [],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )

    rc = mod.export_notebook(str(notebook_path), "html", str(output_path))
    assert rc in (0, 2)
    if rc == 0:
        assert output_path.exists()
