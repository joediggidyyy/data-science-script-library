"""Select an anomaly threshold from score distributions.

Given a CSV with a numeric `score_raw` column (lower = more anomalous),
compute a threshold targeting a desired false-positive rate.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required.")
    sys.exit(1)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate anomaly threshold for target FPR.")
    parser.add_argument("--scores", required=True, type=Path, help="Path to scores.csv (record_id, score_raw)")
    parser.add_argument("--target-fpr", type=float, default=0.01, help="Target False Positive Rate, e.g. 0.01 for 1%%")
    parser.add_argument("--out-report", required=True, type=Path, help="Path to output markdown report")

    args = parser.parse_args()

    scores: List[float] = []
    with args.scores.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                scores.append(float(row["score_raw"]))
            except (ValueError, TypeError, KeyError):
                pass

    if not scores:
        print("Error: No scores found.")
        return 2

    n = len(scores)
    scores_np = np.array(scores)
    target_percentile = args.target_fpr * 100.0
    threshold = float(np.percentile(scores_np, target_percentile))

    n_fp = int(np.sum(scores_np < threshold))
    actual_fpr = float(n_fp / n)

    report = f"""# Threshold Selection Report

**Created (UTC)**: {_utc_now_iso()}
**Dataset**: {args.scores.name}
**Target FPR**: {args.target_fpr * 100:.2f}%
**Logic**: lower score = more anomalous

## Result
- **Selected Threshold**: `{threshold:.6f}`
- **Observed FPR**: {actual_fpr * 100:.4f}% ({n_fp}/{n} records)

## Distribution Stats
- Min: {np.min(scores_np):.6f}
- Max: {np.max(scores_np):.6f}
- Mean: {np.mean(scores_np):.6f}
- Median: {np.median(scores_np):.6f}

## Usage
Scores **lower** than `{threshold:.6f}` are flagged as anomalies.
"""

    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.write_text(report, encoding="utf-8")

    meta = {
        "threshold": threshold,
        "target_fpr": args.target_fpr,
        "actual_fpr": actual_fpr,
        "n_samples": n,
        "algo": "percentile_lower_is_anomaly",
    }

    json_path = args.out_report.with_suffix(".json")
    json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Report written to {args.out_report}")
    print(f"Metadata written to {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
