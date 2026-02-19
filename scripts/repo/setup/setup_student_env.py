#!/usr/bin/env python3
"""setup_student_env.py

Student-friendly Python environment bootstrap for this repository.

Default behavior is non-interactive (safe defaults).
Use --interactive for prompt-driven setup.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class RunResult:
    returncode: int
    stdout: str
    stderr: str


def _python_major_minor(executable: str) -> str:
    try:
        p = subprocess.run(
            [executable, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True,
            check=False,
        )
        if p.returncode == 0:
            return str((p.stdout or "").strip())
    except Exception:
        pass
    return ""


def _run(cmd: List[str], cwd: Path, dry_run: bool = False, verbose: bool = False) -> RunResult:
    if verbose or dry_run:
        print(f"[setup] command: {' '.join(cmd)}")
    if dry_run:
        return RunResult(returncode=0, stdout="", stderr="")
    # Stream child output directly to terminal to avoid stalls on large installers.
    p = subprocess.run(cmd, cwd=str(cwd), check=False)
    return RunResult(returncode=int(p.returncode), stdout="", stderr="")


def _prompt_text(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def _prompt_yes_no(label: str, default_yes: bool = True) -> bool:
    hint = "Y/n" if default_yes else "y/N"
    raw = input(f"{label} ({hint}): ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes"}


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_pip(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "pip.exe"
    return venv_dir / "bin" / "pip"


def _activation_help(venv_dir: Path) -> List[str]:
    rel = venv_dir.name
    if os.name == "nt":
        return [
            f"PowerShell: .\\{rel}\\Scripts\\Activate.ps1",
            f"cmd.exe: {rel}\\Scripts\\activate.bat",
        ]
    return [f"bash/zsh: source {rel}/bin/activate"]


def _starter_notebook_payload(title: str) -> dict:
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"language": "markdown"},
                "source": [
                    f"# {title}",
                    "",
                    "Welcome to your first-week lab notebook.",
                    "",
                    "This notebook was created by `setup_student_env.py` and is designed for a first run in VS Code.",
                    "",
                    "Learning goals:",
                    "- load tiny CSV-like data into Python",
                    "- inspect and summarize values",
                    "- generate a simple plot (with a fallback if plotting libs are missing)",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"language": "python"},
                "outputs": [],
                "source": [
                    "import sys",
                    "print('Python executable:', sys.executable)",
                    "print('Python version:', sys.version)",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {"language": "markdown"},
                "source": [
                    "## Step 1: Load tiny sample data",
                    "",
                    "We will parse a tiny CSV dataset from a string so the notebook runs anywhere.",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"language": "python"},
                "outputs": [],
                "source": [
                    "import csv",
                    "from io import StringIO",
                    "",
                    "raw_csv = '''day,score",
                    "1,72",
                    "2,75",
                    "3,78",
                    "4,74",
                    "5,82",
                    "6,85",
                    "7,88",
                    "'''",
                    "",
                    "rows = list(csv.DictReader(StringIO(raw_csv)))",
                    "days = [int(r['day']) for r in rows]",
                    "scores = [int(r['score']) for r in rows]",
                    "",
                    "print('rows:', len(rows))",
                    "print('first row:', rows[0])",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {"language": "markdown"},
                "source": [
                    "## Step 2: Quick summary stats",
                    "",
                    "We compute min, max, and average using pure Python.",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"language": "python"},
                "outputs": [],
                "source": [
                    "avg_score = sum(scores) / len(scores)",
                    "print('min:', min(scores))",
                    "print('max:', max(scores))",
                    "print('avg:', round(avg_score, 2))",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {"language": "markdown"},
                "source": [
                    "## Step 3: Plot the data",
                    "",
                    "We try `matplotlib` first. If it is not installed, we show a text fallback chart.",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"language": "python"},
                "outputs": [],
                "source": [
                    "try:",
                    "    import matplotlib.pyplot as plt",
                    "    plt.figure(figsize=(7, 4))",
                    "    plt.plot(days, scores, marker='o')",
                    "    plt.title('Weekly Score Trend')",
                    "    plt.xlabel('Day')",
                    "    plt.ylabel('Score')",
                    "    plt.grid(True, alpha=0.3)",
                    "    plt.show()",
                    "    print('Rendered matplotlib plot.')",
                    "except Exception:",
                    "    print('matplotlib not available; showing text chart instead:')",
                    "    lo, hi = min(scores), max(scores)",
                    "    span = max(1, hi - lo)",
                    "    for d, s in zip(days, scores):",
                    "        bar_len = int((s - lo) / span * 30)",
                    "        print(f'Day {d}: ' + '#' * bar_len + f' ({s})')",
                    "    print('Tip: install full dependencies for charting support: pip install -r requirements-full.txt')",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {"language": "markdown"},
                "source": [
                    "## Reflection prompt",
                    "",
                    "In 2-3 sentences, explain what trend you observe and what might cause one low point in the week.",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": f"{sys.version_info.major}.{sys.version_info.minor}",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _load_notebook_template_or_default(repo_root: Path, title: str) -> dict:
    template_path = repo_root / "notebooks" / "first_week_lab_template.ipynb"
    if template_path.exists() and template_path.is_file():
        try:
            return json.loads(template_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return _starter_notebook_payload(title)


def _build_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Create and configure a student-friendly Python + Jupyter setup.")
    ap.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    ap.add_argument("--interactive", action="store_true", help="Prompt for setup choices")
    ap.add_argument("--python", default=sys.executable, help="Python executable used to create venv")
    ap.add_argument("--venv-dir", default=".venv", help="Virtual environment directory")
    ap.add_argument(
        "--deps",
        choices=["core", "full", "tensorflow-class"],
        default="core",
        help="Dependency install profile",
    )
    ap.add_argument("--tensorflow-package", default="tensorflow", help="TensorFlow package name for tensorflow-class profile")
    ap.add_argument("--kernel-name", default="dssl", help="Jupyter kernel name")
    ap.add_argument("--kernel-display", default="Python (data-science-script-library)", help="Jupyter kernel display name")
    ap.add_argument("--notebook-path", default="notebooks/first_week_lab.ipynb", help="Starter notebook path")
    ap.add_argument("--skip-notebook", action="store_true", help="Do not create starter notebook")
    ap.add_argument("--skip-kernel", action="store_true", help="Do not register ipykernel")
    ap.add_argument("--upgrade-pip", action="store_true", help="Upgrade pip/setuptools/wheel in venv")
    ap.add_argument("--dry-run", action="store_true", help="Show actions without executing")
    ap.add_argument("--verbose", action="store_true", help="Verbose command output")
    return ap.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    ns = _build_args(argv)
    repo_root = Path(ns.repo_root).resolve()

    if ns.interactive:
        print("\nWelcome! We'll set up Python + Jupyter for this project step by step.\n")
        ns.venv_dir = _prompt_text("Virtual environment folder", ns.venv_dir)
        ns.deps = _prompt_text("Dependency profile (core/full/tensorflow-class)", ns.deps).strip().lower() or "core"
        if ns.deps not in {"core", "full", "tensorflow-class"}:
            print("[setup] Invalid dependency profile. Use core, full, or tensorflow-class.")
            return 2
        ns.upgrade_pip = _prompt_yes_no("Upgrade pip, setuptools, and wheel", default_yes=True)
        create_kernel = _prompt_yes_no("Register a Jupyter kernel for VS Code", default_yes=True)
        ns.skip_kernel = not create_kernel
        if create_kernel:
            ns.kernel_name = _prompt_text("Kernel name", ns.kernel_name)
            ns.kernel_display = _prompt_text("Kernel display name", ns.kernel_display)
        create_notebook = _prompt_yes_no("Create a starter notebook file", default_yes=True)
        ns.skip_notebook = not create_notebook
        if create_notebook:
            ns.notebook_path = _prompt_text("Starter notebook path", ns.notebook_path)

    venv_dir = (repo_root / ns.venv_dir).resolve()
    py = str(Path(ns.python).resolve())

    py_mm = _python_major_minor(py)
    if ns.deps == "tensorflow-class" and py_mm != "3.13":
        print("[setup] tensorflow-class profile requires Python 3.13.")
        print(f"[setup] Selected interpreter reports: {py_mm or 'unknown'}")
        print("[setup] Provide a Python 3.13 interpreter with --python.")
        return 2

    print(f"[setup] repo root: {repo_root}")
    print(f"[setup] venv path: {venv_dir}")
    print(f"[setup] dependency profile: {ns.deps}")

    create_res = _run([py, "-m", "venv", str(venv_dir)], cwd=repo_root, dry_run=ns.dry_run, verbose=ns.verbose)
    if create_res.returncode != 0:
        print("[setup] Failed to create virtual environment.")
        return 2

    venv_python = _venv_python(venv_dir)
    venv_pip = _venv_pip(venv_dir)

    if ns.upgrade_pip:
        up_res = _run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            cwd=repo_root,
            dry_run=ns.dry_run,
            verbose=ns.verbose,
        )
        if up_res.returncode != 0:
            print("[setup] Failed to upgrade pip tooling.")
            return 2

    req_file = "requirements-full.txt" if ns.deps in {"full", "tensorflow-class"} else "requirements.txt"
    deps_res = _run([str(venv_pip), "install", "-r", req_file], cwd=repo_root, dry_run=ns.dry_run, verbose=ns.verbose)
    if deps_res.returncode != 0:
        print(f"[setup] Failed to install dependencies from {req_file}.")
        return 2

    if ns.deps == "tensorflow-class":
        tf_res = _run([str(venv_pip), "install", ns.tensorflow_package], cwd=repo_root, dry_run=ns.dry_run, verbose=ns.verbose)
        if tf_res.returncode != 0:
            print(f"[setup] Failed to install TensorFlow package: {ns.tensorflow_package}.")
            return 2

    jup_res = _run([str(venv_pip), "install", "ipykernel", "jupyter"], cwd=repo_root, dry_run=ns.dry_run, verbose=ns.verbose)
    if jup_res.returncode != 0:
        print("[setup] Failed to install Jupyter tooling in the virtual environment.")
        return 2

    if not ns.skip_kernel:
        kernel_res = _run(
            [
                str(venv_python),
                "-m",
                "ipykernel",
                "install",
                "--user",
                "--name",
                ns.kernel_name,
                "--display-name",
                ns.kernel_display,
            ],
            cwd=repo_root,
            dry_run=ns.dry_run,
            verbose=ns.verbose,
        )
        if kernel_res.returncode != 0:
            print("[setup] Failed to register Jupyter kernel.")
            return 2

    if not ns.skip_notebook:
        nb_path = (repo_root / ns.notebook_path).resolve()
        nb_payload = _load_notebook_template_or_default(repo_root, "First Week Lab: Data Load + Simple Plot")
        if ns.dry_run:
            print(f"[setup] would create notebook: {nb_path}")
        else:
            nb_path.parent.mkdir(parents=True, exist_ok=True)
            nb_path.write_text(json.dumps(nb_payload, indent=2), encoding="utf-8")
            print(f"[setup] wrote notebook: {nb_path}")

    print("\n[setup] Completed successfully.")
    print("[setup] Activation command(s):")
    for ln in _activation_help(venv_dir):
        print(f"  - {ln}")
    print("[setup] Next in VS Code:")
    print("  1) Open this folder in VS Code.")
    print("  2) Install extensions: Python + Jupyter (if not already installed).")
    print("  3) Open the notebook file and choose the kernel you just created.")
    print("  4) Run the first code cell to verify Python is coming from your venv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
