from __future__ import annotations

import json
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_audit_env_var_registry_reports_unregistered_names(tmp_path: Path) -> None:
    script_path = scripts_root() / "repo" / "audit" / "audit_env_var_registry.py"
    mod = import_module_from_path("audit_env_var_registry", script_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "script.py").write_text(
        "import os\n"
        "os.getenv('MYAPP_TOKEN')\n"
        "os.environ.get('MYAPP_EXTRA')\n",
        encoding="utf-8",
    )
    (repo_root / "notes.md").write_text(
        "Use `MYAPP_ALIAS` and `${MYAPP_EXTRA}` in examples.\n",
        encoding="utf-8",
    )

    registry_path = tmp_path / "env_registry.json"
    registry_path.write_text(
        json.dumps({"vars": {"MYAPP_TOKEN": {"aliases": ["MYAPP_ALIAS"]}}}),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    rc = mod.main([
        "--repo-root",
        str(repo_root),
        "--registry-json",
        str(registry_path),
        "--project-prefix",
        "MYAPP_",
        "--output-dir",
        str(out_dir),
        "--stamp",
        "TESTSTAMP",
    ])
    assert rc == 0

    report_json = out_dir / "env_var_registry_audit_TESTSTAMP.json"
    report_md = out_dir / "env_var_registry_audit_TESTSTAMP.md"
    assert report_json.exists()
    assert report_md.exists()

    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["counts"]["registry_names"] == 1
    assert payload["counts"]["registry_aliases"] == 1
    assert payload["prefix_summary"]["MYAPP"] >= 2
    names = [row["name"] for row in payload["unregistered_project_scoped"]]
    assert "MYAPP_EXTRA" in names


def test_audit_env_var_registry_dry_run_without_registry(tmp_path: Path, capsys) -> None:
    script_path = scripts_root() / "repo" / "audit" / "audit_env_var_registry.py"
    mod = import_module_from_path("audit_env_var_registry_dry", script_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "script.py").write_text("import os\nos.getenv('DEMO_VALUE')\n", encoding="utf-8")

    rc = mod.main(["--repo-root", str(repo_root), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "DEMO_VALUE" in payload["observed_vars"]