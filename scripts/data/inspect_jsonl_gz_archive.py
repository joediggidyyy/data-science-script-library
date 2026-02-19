"""Inspect a gzipped JSONL archive (.jsonl.gz).

Outputs a compact names-only summary: record count, key frequencies, and
optional sample records.
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


def _safe_path_ref(path: Path) -> str:
    try:
        return path.as_posix()
    except Exception:
        return path.name


def inspect_data(path: Path, *, sample: int = 1, top: int = 20) -> int:
    if not path.exists():
        print(f"[FAIL] File not found: {_safe_path_ref(path)}")
        return 2

    print(f"Inspecting: {_safe_path_ref(path)}")

    count = 0
    keys_counter: Counter[str] = Counter()
    sample_records: List[Dict[str, Any]] = []

    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue
                if not isinstance(record, dict):
                    continue

                count += 1
                keys_counter.update(str(k) for k in record.keys())
                if len(sample_records) < max(0, int(sample)):
                    sample_records.append(record)
    except Exception as exc:
        print(f"[FAIL] Error reading archive: {exc}")
        return 2

    print(f"Total Records: {count}")
    print(f"Key Frequency (top {int(top)}):")
    for k, v in keys_counter.most_common(max(0, int(top))):
        print(f"  {k}: {v}")

    if sample_records:
        print("Sample Record 1 Keys:")
        print(list(sample_records[0].keys()))
        print("Sample Record 1 Content:")
        print(json.dumps(sample_records[0], indent=2, ensure_ascii=True))

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a gzipped JSONL archive file")
    parser.add_argument("path", type=Path, help="Path to .jsonl.gz archive")
    parser.add_argument("--sample", type=int, default=1, help="Number of sample records to print (default: 1)")
    parser.add_argument("--top", type=int, default=20, help="Top-N keys to show (default: 20)")
    args = parser.parse_args(argv)

    return inspect_data(args.path, sample=int(args.sample), top=int(args.top))


if __name__ == "__main__":
    raise SystemExit(main())
