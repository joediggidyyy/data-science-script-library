#!/usr/bin/env python3
"""inventory_json_to_csv.py

## NAME

inventory_json_to_csv — convert a script inventory JSON to CSV

## SYNOPSIS

python inventory_json_to_csv.py <in_json> <out_csv>

## DESCRIPTION

Converts an inventory JSON file produced by `generate_script_inventory.py` into CSV.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import csv
import json
from pathlib import Path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Convert inventory JSON to CSV")
    parser.add_argument("in_json", help="Input inventory JSON")
    parser.add_argument("out_csv", help="Output CSV")
    args = parser.parse_args()

    in_path = Path(args.in_json)
    out_path = Path(args.out_csv)

    data = json.loads(in_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])

    # stable fields
    fields = ["path", "size_bytes", "last_modified_utc", "last_commit_iso", "description"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for e in entries:
            w.writerow({k: e.get(k, "") for k in fields})

    print(f"Wrote {len(entries)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
