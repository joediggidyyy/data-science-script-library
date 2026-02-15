# Repo helpers

Repository analysis helpers (inventory, duplication, hygiene).

These scripts are “report-first” utilities: they produce artifacts you can review and share.

## Included tools

- `inventory/` — build inventories of scripts/files and export to CSV
- `analysis/` — code analysis utilities (duplicate detection)

## Usage examples

Generate a script inventory (JSON + Markdown):

```text
python scripts/repo/inventory/generate_script_inventory.py --root . --out report_tmp/inventory
```

Find exact duplicate functions in a Python codebase:

```text
python scripts/repo/analysis/find_duplicate_functions.py --root . --out report_tmp/dupes
```

