"""parquet_inspect.py

Inspect a Parquet file (schema + high-level metadata).

This script uses `pyarrow` when available. If `pyarrow` is not installed,
inspection is not possible and the script will exit with a helpful message.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class ParquetSummary:
    path: str
    size_bytes: int
    num_rows: int
    num_columns: int
    num_row_groups: int
    columns: List[str]
    schema: str


def _import_pyarrow_parquet():
    try:
        import pyarrow.parquet as pq  # type: ignore

        return pq
    except Exception as e:
        raise RuntimeError(
            "Missing dependency: pyarrow. Install pyarrow to inspect Parquet files."
        ) from e


def inspect_parquet(path: Path) -> ParquetSummary:
    pq = _import_pyarrow_parquet()

    path = path.resolve()
    pf = pq.ParquetFile(str(path))

    md = pf.metadata
    if md is None:
        # Extremely unusual, but handle defensively.
        raise RuntimeError("Parquet metadata not available")

    schema = pf.schema_arrow
    columns = [field.name for field in schema]

    return ParquetSummary(
        path=str(path),
        size_bytes=path.stat().st_size,
        num_rows=int(md.num_rows),
        num_columns=int(md.num_columns),
        num_row_groups=int(md.num_row_groups),
        columns=columns,
        schema=str(schema),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a Parquet file")
    parser.add_argument("parquet", help="Path to .parquet file")
    parser.add_argument(
        "--json",
        default=None,
        help="Optional JSON output path (otherwise prints a human summary)",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    path = Path(args.parquet)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        summary = inspect_parquet(path)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
        print(f"Wrote: {out}")
        return 0

    # Human summary
    print(f"Path: {summary.path}")
    print(f"Size: {summary.size_bytes} bytes")
    print(f"Rows: {summary.num_rows}")
    print(f"Columns ({summary.num_columns}): {', '.join(summary.columns)}")
    print(f"Row groups: {summary.num_row_groups}")
    print("Schema:")
    print(summary.schema)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
