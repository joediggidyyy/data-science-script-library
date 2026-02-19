# Repo helpers

Repository analysis helpers (inventory, duplication, hygiene).

These scripts are “report-first” utilities: they produce artifacts you can review and share.

## Included tools

- `inventory/` — build inventories of scripts/files and export to CSV
- `analysis/` — code analysis utilities (duplicate detection)
- `audit/` — operational audit utilities (log evidence + remediation triage)

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

