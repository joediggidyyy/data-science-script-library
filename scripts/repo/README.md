# Repo helpers

Repository analysis helpers (inventory, duplication, hygiene).

These scripts are “report-first” utilities: they produce artifacts you can review and share.

## Included tools

- `inventory/` — build inventories of scripts/files and export to CSV
- `analysis/` — code analysis utilities (duplicate detection)
- `audit/` — operational audit utilities (log evidence + remediation triage)
- `setup/` — student-friendly environment bootstrap (venv + Jupyter setup)

## Usage examples

Generate a script inventory (JSON + Markdown):

```text
python scripts/repo/inventory/generate_script_inventory.py --root . --out report_tmp/inventory
```

Find exact duplicate functions in a Python codebase:

```text
python scripts/repo/analysis/find_duplicate_functions.py --root . --out report_tmp/dupes
```

Audit VS Code crash logs (dry-run):

```text
python scripts/repo/audit/audit_vscode_crash_logs.py --dry-run
```

Generate remediation triage from latest crash evidence:

```text
python scripts/repo/audit/triage_vscode_crash_remediation.py --dry-run
```

Audit repository hygiene snapshot:

```text
python scripts/repo/audit/audit_repo_health_snapshot.py --repo-root . --dry-run
```

Audit runtime artifacts snapshot:

```text
python scripts/repo/audit/audit_runtime_artifacts_snapshot.py --runtime-root . --heartbeat watchdog=health/watchdog.heartbeat --dry-run
```

Audit status drift against task SSOT + dashboard:

```text
python scripts/repo/audit/audit_status_drift.py --tasks-json operations/tasks.json --dashboard-md docs/dashboards/room/JOBS_DASHBOARD.md --dry-run
```

Report runtime parameter surface (names-only):

```text
python scripts/repo/audit/report_runtime_parameters.py --runtime-root . --env-name OPENAI_API_KEY --check-path logs/health/watchdog.heartbeat --dry-run
```

Audit web dashboard endpoints (names-only):

```text
python scripts/repo/audit/audit_web_dashboard_endpoints.py --base-url http://127.0.0.1:8899 --endpoint / --endpoint /health --dry-run
```

Check process PID files:

```text
python scripts/repo/audit/check_pidfiles_status.py --pidfile agent=./agent.pid --pidfile dashboard=./dashboard.pid --json
```

Set up an environment for coursework (default non-interactive):

```text
python scripts/repo/setup/setup_student_env.py
```

TensorFlow class profile (Python 3.13 required):

```text
python scripts/repo/setup/setup_student_env.py --deps tensorflow-class --python <python3.13>
```

## Related docs

- Setup/tutorial hub: `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
- Security guidance: `SECURITY.md`

