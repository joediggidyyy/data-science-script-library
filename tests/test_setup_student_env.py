from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_setup_student_env_help_runs() -> None:
    script = scripts_root() / "repo" / "setup" / "setup_student_env.py"
    res = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "--interactive" in res.stdout
    assert "--notebook-path" in res.stdout
    assert "tensorflow-class" in res.stdout


def test_setup_student_env_dry_run_defaults_to_first_week_lab(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "setup" / "setup_student_env.py"

    # Minimal placeholders so repo-root looks realistic (script is dry-run, so no installs happen).
    (tmp_path / "requirements.txt").write_text("\n", encoding="utf-8")
    (tmp_path / "requirements-full.txt").write_text("\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--dry-run"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr
    assert "first_week_lab.ipynb" in res.stdout


def test_setup_student_env_loads_template_if_present(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "setup" / "setup_student_env.py"
    mod = import_module_from_path("test_setup_student_env_mod", script)

    notebooks_dir = tmp_path / "notebooks"
    notebooks_dir.mkdir(parents=True, exist_ok=True)
    template = notebooks_dir / "first_week_lab_template.ipynb"
    template_payload = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"language": "markdown"},
                "source": ["# Sentinel template"],
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    template.write_text(json.dumps(template_payload), encoding="utf-8")

    loaded = mod._load_notebook_template_or_default(tmp_path, "Ignored title")
    assert loaded["cells"][0]["source"][0] == "# Sentinel template"


def test_setup_student_env_default_payload_includes_cell_language_metadata() -> None:
    script = scripts_root() / "repo" / "setup" / "setup_student_env.py"
    mod = import_module_from_path("test_setup_student_env_mod_lang", script)

    payload = mod._starter_notebook_payload("Notebook Title")
    assert isinstance(payload.get("cells"), list)
    assert len(payload["cells"]) >= 2

    for idx, cell in enumerate(payload["cells"], start=1):
        assert isinstance(cell.get("metadata"), dict), f"cell {idx} missing metadata object"
        assert isinstance(cell["metadata"].get("language"), str), f"cell {idx} missing metadata.language"


def test_setup_student_env_tensorflow_profile_requires_python_313(tmp_path: Path) -> None:
    script = scripts_root() / "repo" / "setup" / "setup_student_env.py"

    (tmp_path / "requirements.txt").write_text("\n", encoding="utf-8")
    (tmp_path / "requirements-full.txt").write_text("\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(tmp_path),
            "--deps",
            "tensorflow-class",
            "--dry-run",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 2
    assert "requires Python 3.13" in (res.stdout + res.stderr)
