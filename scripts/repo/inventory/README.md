# Inventory

Generate a machine-readable inventory of scripts and export it to formats suitable for review.

## Included scripts

- `generate_script_inventory.py` — Scan a directory for scripts and emit JSON + Markdown inventory.
- `inventory_json_to_csv.py` — Convert an inventory JSON file to CSV.

## Usage examples

Generate inventory artifacts:

```text
python scripts/repo/inventory/generate_script_inventory.py --root . --out report_tmp/inventory
```

Include git last-commit timestamps (requires `git` and a repo root):

```text
python scripts/repo/inventory/generate_script_inventory.py --root . --out report_tmp/inventory --use-git
```

Convert the JSON inventory to CSV:

```text
python scripts/repo/inventory/inventory_json_to_csv.py report_tmp/inventory/script_inventory.json report_tmp/inventory/script_inventory.csv
```

