"""data_cleaning_recipes.py

Small, dependency-light CSV cleaning recipes.

This script is intentionally conservative (and easy to audit) compared to full
ETL frameworks. It's designed for quick cleanup before analysis.

Features (opt-in via flags):
- Normalize column names (snake_case-ish)
- Trim whitespace in all fields
- Drop empty rows
- Drop duplicate rows
- Drop/keep specific columns

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass
class CleanReport:
    input_path: str
    output_path: str
    rows_in: int
    rows_out: int
    empty_rows_dropped: int
    duplicate_rows_dropped: int
    columns_in: List[str]
    columns_out: List[str]
    renamed_columns: Dict[str, str]
    dropped_columns: List[str]


def normalize_column_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "col"


def _dedupe_names(names: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    out: List[str] = []
    for n in names:
        if n not in seen:
            seen[n] = 0
            out.append(n)
        else:
            seen[n] += 1
            out.append(f"{n}_{seen[n]}")
    return out


def clean_csv(
    input_path: Path,
    output_path: Path,
    *,
    normalize_columns: bool,
    trim_whitespace: bool,
    drop_empty_rows: bool,
    drop_duplicate_rows: bool,
    drop_columns: Optional[Sequence[str]] = None,
    keep_columns: Optional[Sequence[str]] = None,
    encoding: str = "utf-8",
) -> CleanReport:
    input_path = input_path.resolve()
    output_path = output_path.resolve()

    drop_set = set(drop_columns or [])
    keep_set = set(keep_columns or [])
    if drop_set and keep_set:
        raise ValueError("Use either drop_columns or keep_columns, not both")

    rows_in = 0
    rows_out = 0
    empty_rows_dropped = 0
    duplicate_rows_dropped = 0

    with input_path.open("r", encoding=encoding, newline="") as rf:
        reader = csv.DictReader(rf)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")

        original_cols = list(reader.fieldnames)

        renamed_map: Dict[str, str] = {}
        cols = original_cols
        if normalize_columns:
            normalized = [normalize_column_name(c) for c in cols]
            normalized = _dedupe_names(normalized)
            renamed_map = dict(zip(cols, normalized))
            cols = normalized

        if keep_set:
            cols_out = [c for c in cols if c in keep_set]
        else:
            cols_out = [c for c in cols if c not in drop_set]

        dropped_columns: List[str] = [c for c in cols if c not in cols_out]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding=encoding, newline="") as wf:
            writer = csv.DictWriter(wf, fieldnames=cols_out)
            writer.writeheader()

            seen_rows: Set[Tuple[str, ...]] = set()

            for row in reader:
                rows_in += 1

                # Rename keys if needed
                if normalize_columns:
                    row = {renamed_map.get(k, k): v for k, v in row.items()}

                # Trim whitespace
                if trim_whitespace:
                    for k, v in list(row.items()):
                        if isinstance(v, str):
                            row[k] = v.strip()

                # Filter columns
                if cols_out != cols:
                    row = {k: row.get(k, "") for k in cols_out}

                # Drop empty rows
                if drop_empty_rows:
                    if all((row.get(k) or "").strip() == "" for k in cols_out):
                        empty_rows_dropped += 1
                        continue

                # Drop duplicates
                if drop_duplicate_rows:
                    key = tuple((row.get(k) or "") for k in cols_out)
                    if key in seen_rows:
                        duplicate_rows_dropped += 1
                        continue
                    seen_rows.add(key)

                writer.writerow(row)
                rows_out += 1

    return CleanReport(
        input_path=str(input_path),
        output_path=str(output_path),
        rows_in=rows_in,
        rows_out=rows_out,
        empty_rows_dropped=empty_rows_dropped,
        duplicate_rows_dropped=duplicate_rows_dropped,
        columns_in=original_cols,
        columns_out=cols_out,
        renamed_columns=renamed_map,
        dropped_columns=dropped_columns,
    )


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + ".clean.csv")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Apply small CSV cleaning recipes")
    parser.add_argument("csv", help="Input CSV path")
    parser.add_argument("--out", default=None, help="Output CSV path")
    parser.add_argument(
        "--report",
        default=None,
        help="Output JSON report path (default: <out>.clean_report.json)",
    )

    parser.add_argument("--normalize-columns", action="store_true")
    parser.add_argument("--trim-whitespace", action="store_true")
    parser.add_argument("--drop-empty-rows", action="store_true")
    parser.add_argument("--drop-duplicate-rows", action="store_true")
    parser.add_argument(
        "--drop-columns",
        default=None,
        help="Comma-separated columns to drop (applied after normalization)",
    )
    parser.add_argument(
        "--keep-columns",
        default=None,
        help="Comma-separated columns to keep (applied after normalization)",
    )
    parser.add_argument("--encoding", default="utf-8")

    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = Path(args.csv)
    if not input_path.exists():
        print(f"Error: CSV not found: {input_path}", file=sys.stderr)
        return 2

    output_path = Path(args.out) if args.out else _default_output_path(input_path)

    def _split_opt(value: Optional[str]) -> Optional[List[str]]:
        if value is None:
            return None
        parts = [p.strip() for p in value.split(",") if p.strip()]
        return parts

    try:
        report = clean_csv(
            input_path,
            output_path,
            normalize_columns=bool(args.normalize_columns),
            trim_whitespace=bool(args.trim_whitespace),
            drop_empty_rows=bool(args.drop_empty_rows),
            drop_duplicate_rows=bool(args.drop_duplicate_rows),
            drop_columns=_split_opt(args.drop_columns),
            keep_columns=_split_opt(args.keep_columns),
            encoding=str(args.encoding),
        )
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    report_path = Path(args.report) if args.report else output_path.with_suffix(".clean_report.json")
    report_path.write_text(json.dumps(asdict(report), indent=2), encoding=str(args.encoding))

    print(f"Wrote: {output_path}")
    print(f"Report: {report_path}")
    print(f"Rows: {report.rows_in} -> {report.rows_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
