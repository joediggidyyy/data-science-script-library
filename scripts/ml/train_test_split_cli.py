#!/usr/bin/env python3
"""train_test_split_cli.py

## NAME

train_test_split_cli — deterministic train/test split for CSV datasets (optionally stratified)

## SYNOPSIS

python train_test_split_cli.py <in_csv> --out <out_dir> [--test-size 0.2] [--seed 1337]
                               [--stratify-col label] [--delimiter ,]

## DESCRIPTION

This script performs a reproducible train/test split for CSV datasets.

Features:
- deterministic shuffling via `--seed`
- optional stratification by a column (e.g., a class label)
- writes `train.csv` and `test.csv`
- optionally writes `split_indices.json` (row indices relative to the input, excluding header)

Notes:
- This tool is intentionally dependency-free (no pandas required).
- For stratification, the CSV is read into memory to compute group counts.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class SplitResult:
    train_indices: list[int]
    test_indices: list[int]


def _parse_test_size(test_size: str) -> tuple[str, float | int]:
    """Return (kind, value) where kind is 'fraction' or 'count'."""

    s = test_size.strip()
    if s == "":
        raise ValueError("test_size must not be empty")

    # Accept integers like "10" as counts.
    if s.isdigit():
        n = int(s)
        if n < 0:
            raise ValueError("test_size count must be >= 0")
        return "count", n

    # Otherwise parse as float fraction.
    p = float(s)
    if not (0.0 <= p <= 1.0):
        raise ValueError("test_size fraction must be between 0 and 1")
    return "fraction", p


def _allocate_counts_proportionally(total_test: int, bucket_sizes: dict[str, int]) -> dict[str, int]:
    """Allocate an exact test count across buckets, proportional to bucket sizes.

    Uses largest-remainder method to ensure sum(counts) == total_test.
    Deterministic given bucket_sizes ordering.
    """

    if total_test <= 0:
        return {k: 0 for k in bucket_sizes.keys()}

    total = sum(bucket_sizes.values())
    if total == 0:
        return {k: 0 for k in bucket_sizes.keys()}

    raw: dict[str, float] = {k: (bucket_sizes[k] / total) * total_test for k in bucket_sizes.keys()}
    base: dict[str, int] = {k: int(raw[k]) for k in bucket_sizes.keys()}

    remainder = total_test - sum(base.values())
    if remainder <= 0:
        return base

    # Largest fractional remainder first.
    fracs = sorted(
        ((k, raw[k] - base[k]) for k in bucket_sizes.keys()),
        key=lambda kv: (kv[1], kv[0]),
        reverse=True,
    )
    for i in range(remainder):
        base[fracs[i % len(fracs)][0]] += 1

    return base


def split_indices(
    n_rows: int,
    *,
    test_size: float | int,
    seed: int,
    stratify: Optional[list[str]] = None,
) -> SplitResult:
    """Compute train/test indices for n_rows.

    If stratify is provided, it must be a list of length n_rows with the
    stratification label per row.
    """

    rng = random.Random(seed)

    if isinstance(test_size, float):
        total_test = int(round(test_size * n_rows))
    else:
        total_test = int(test_size)

    total_test = max(0, min(total_test, n_rows))

    if n_rows == 0:
        return SplitResult(train_indices=[], test_indices=[])

    if stratify is None:
        all_idx = list(range(n_rows))
        rng.shuffle(all_idx)
        test_idx = set(all_idx[:total_test])
        train = [i for i in range(n_rows) if i not in test_idx]
        test = [i for i in range(n_rows) if i in test_idx]
        return SplitResult(train_indices=train, test_indices=test)

    if len(stratify) != n_rows:
        raise ValueError("stratify labels length must equal number of rows")

    # Group indices by label.
    buckets: dict[str, list[int]] = {}
    for i, label in enumerate(stratify):
        key = str(label)
        buckets.setdefault(key, []).append(i)

    # Deterministic ordering by key.
    bucket_sizes = {k: len(v) for k, v in sorted(buckets.items(), key=lambda kv: kv[0])}
    per_bucket_test = _allocate_counts_proportionally(total_test, bucket_sizes)

    test_set: set[int] = set()

    for k in bucket_sizes.keys():
        idxs = list(buckets[k])
        rng.shuffle(idxs)
        take = min(per_bucket_test.get(k, 0), len(idxs))
        test_set.update(idxs[:take])

    # If rounding/edge cases left us short/over, fix by sampling from remaining.
    # (This should be rare but keeps invariants correct.)
    if len(test_set) < total_test:
        remaining = [i for i in range(n_rows) if i not in test_set]
        rng.shuffle(remaining)
        need = total_test - len(test_set)
        test_set.update(remaining[:need])
    elif len(test_set) > total_test:
        extra = list(test_set)
        rng.shuffle(extra)
        for i in extra[: len(test_set) - total_test]:
            test_set.remove(i)

    train = [i for i in range(n_rows) if i not in test_set]
    test = [i for i in range(n_rows) if i in test_set]
    return SplitResult(train_indices=train, test_indices=test)


def _read_csv_rows(path: Path, *, encoding: str, delimiter: str) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV appears to have no header row")
        header = list(reader.fieldnames)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({k: (row.get(k) or "") for k in header})
        return header, rows


def _write_csv(path: Path, header: list[str], rows: Iterable[dict[str, str]], *, encoding: str, delimiter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header, delimiter=delimiter)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic train/test split for CSV datasets")
    parser.add_argument("in_csv", help="Input CSV file")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--test-size", default="0.2", help="Test size as fraction (0-1) or integer count")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for deterministic shuffling")
    parser.add_argument("--stratify-col", default=None, help="Column name to stratify by")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: ,)")
    parser.add_argument("--encoding", default="utf-8", help="Text encoding (default: utf-8)")
    parser.add_argument("--prefix", default="", help="Optional prefix for output files")
    parser.add_argument(
        "--write-indices",
        action="store_true",
        help="Write split_indices.json (row indices relative to input, excluding header)",
    )
    parser.add_argument(
        "--preserve-order",
        action="store_true",
        help="Preserve original row order in output files (default: false; outputs follow selection order)",
    )

    args = parser.parse_args(argv)

    in_path = Path(args.in_csv).resolve()
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    kind, ts = _parse_test_size(args.test_size)
    test_size: float | int = ts

    header, rows = _read_csv_rows(in_path, encoding=args.encoding, delimiter=args.delimiter)

    stratify_labels: Optional[list[str]] = None
    if args.stratify_col:
        if args.stratify_col not in header:
            raise ValueError(f"stratify-col '{args.stratify_col}' not in CSV header")
        stratify_labels = [r.get(args.stratify_col, "") for r in rows]

    result = split_indices(len(rows), test_size=test_size, seed=args.seed, stratify=stratify_labels)

    train_idx = result.train_indices
    test_idx = result.test_indices

    if args.preserve_order:
        train_idx = sorted(train_idx)
        test_idx = sorted(test_idx)

    train_rows = [rows[i] for i in train_idx]
    test_rows = [rows[i] for i in test_idx]

    prefix = args.prefix
    out_dir = Path(args.out).resolve()

    train_path = out_dir / f"{prefix}train.csv"
    test_path = out_dir / f"{prefix}test.csv"

    _write_csv(train_path, header, train_rows, encoding=args.encoding, delimiter=args.delimiter)
    _write_csv(test_path, header, test_rows, encoding=args.encoding, delimiter=args.delimiter)

    if args.write_indices:
        idx_path = out_dir / f"{prefix}split_indices.json"
        payload = {
            "input": {"path": str(in_path)},
            "seed": args.seed,
            "test_size": args.test_size,
            "stratify_col": args.stratify_col,
            "train_indices": train_idx,
            "test_indices": test_idx,
        }
        idx_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote: {idx_path}")

    print(f"Wrote: {train_path} ({len(train_rows)} rows)")
    print(f"Wrote: {test_path} ({len(test_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
