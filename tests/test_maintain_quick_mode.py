from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import public_repo_root


def _seed_minimal_repo(root: Path) -> None:
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## 2026-02-19\n\n- baseline\n", encoding="utf-8")


def test_maintain_quick_dry_run_ok(tmp_path: Path) -> None:
    script = public_repo_root() / "maintain.py"
    _seed_minimal_repo(tmp_path)

    res = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--quick", "--dry-run"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0, res.stderr


def test_maintain_quick_strict_fails_on_future_dated_changelog(tmp_path: Path) -> None:
    script = public_repo_root() / "maintain.py"
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## 2099-01-01\n\n- future\n", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--quick", "--dry-run", "--strict"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert res.returncode == 1, res.stderr
