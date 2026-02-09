"""Deprecated alias: use jsonl_to_csv.py.

This module remains for backwards compatibility. Prefer:

    scripts/data/jsonl_to_csv.py

Historically, this script converted a LinkageTracker-style metrics JSONL file
into a dashboard-friendly CSV with a stable column order.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from jsonl_to_csv import jsonl_to_csv


DEFAULT_FIELDS = [
    "timestamp",
    "total_links",
    "broken_links",
    "usage_volume",
    "avg_usage_per_link",
    "link_density",
    "estimated_cost_savings",
    "classification_weighted_savings",
    "sensitivity_weighted_priority",
    "resolved_rate",
    "extra",
]


def export_to_csv(in_path: Path, out_path: Path, fields: Iterable[str] = DEFAULT_FIELDS) -> int:
    """Export JSONL metrics to CSV using a fixed, stable column order."""

    return jsonl_to_csv(in_path, out_path, fields=list(fields))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export linkage metrics JSONL history to CSV")
    parser.add_argument("in_jsonl", help="Input JSONL file")
    parser.add_argument("out_csv", help="Output CSV file")
    args = parser.parse_args()
    count = export_to_csv(Path(args.in_jsonl), Path(args.out_csv))
    print(f"Wrote {count} rows to {args.out_csv}")
    print("NOTE: metrics_exporter.py is deprecated; use jsonl_to_csv.py going forward.")
