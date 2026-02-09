"""JSONL to CSV converter.

This is a small, dependency-free helper that converts newline-delimited JSON
records (JSONL) into a CSV file.

It is designed for the common case in student projects:
- each line is a JSON object (a dict)
- keys are mostly stable but may evolve over time
- some values may be nested dict/list structures

Behavior:
- If you provide an explicit field list, the CSV will contain exactly those
  columns, in that order.
- Otherwise, the script will infer a stable column order by scanning the file
  top-to-bottom and recording keys as they first appear.
- Nested dict/list values are serialized as JSON strings so structure is not
  lost.

Examples:
    python scripts/data/jsonl_to_csv.py logs.jsonl logs.csv
    python scripts/data/jsonl_to_csv.py logs.jsonl logs.csv --fields timestamp,event,latency_ms

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable, Iterator, Optional


def _iter_jsonl(path: Path, *, encoding: str = "utf-8") -> Iterator[dict]:
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding=encoding) as fh:
        for line_no, line in enumerate(fh, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_no} in {path}") from e

            if not isinstance(obj, dict):
                raise ValueError(
                    f"Expected each JSONL record to be an object/dict; got {type(obj).__name__} on line {line_no}"
                )
            yield obj


def infer_fields(records: Iterable[dict]) -> list[str]:
    """Infer a stable field order from JSONL records.

    Order is the order of first appearance of keys while scanning records.
    """

    fields: list[str] = []
    seen: set[str] = set()

    for rec in records:
        for key in rec.keys():
            if key not in seen:
                seen.add(key)
                fields.append(key)

    return fields


def _csv_safe(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def jsonl_to_csv(
    in_path: Path,
    out_path: Path,
    *,
    fields: Optional[Iterable[str]] = None,
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> int:
    """Convert a JSONL file to CSV. Returns number of rows written."""

    records = list(_iter_jsonl(in_path, encoding=encoding))

    if fields is None:
        fieldnames = infer_fields(records)
    else:
        fieldnames = list(fields)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding=encoding) as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        for rec in records:
            row = {k: _csv_safe(rec.get(k, "")) for k in fieldnames}
            writer.writerow(row)

    return len(records)


def _parse_fields_csv(s: str) -> list[str]:
    # Accept either "a,b,c" or "a, b, c".
    return [p.strip() for p in s.split(",") if p.strip()]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert JSONL (one JSON object per line) to CSV",
    )
    parser.add_argument("in_jsonl", help="Input JSONL file")
    parser.add_argument("out_csv", help="Output CSV file")
    parser.add_argument(
        "--fields",
        help="Comma-separated field list to enforce (example: timestamp,event,latency_ms). If omitted, fields are inferred.",
        default=None,
    )
    parser.add_argument(
        "--encoding",
        help="Text encoding for input/output files (default: utf-8)",
        default="utf-8",
    )
    parser.add_argument(
        "--delimiter",
        help="CSV delimiter character (default: ,)",
        default=",",
    )

    args = parser.parse_args(argv)

    fields = _parse_fields_csv(args.fields) if args.fields else None

    count = jsonl_to_csv(
        Path(args.in_jsonl),
        Path(args.out_csv),
        fields=fields,
        encoding=args.encoding,
        delimiter=args.delimiter,
    )
    print(f"Wrote {count} rows to {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
