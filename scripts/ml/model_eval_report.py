#!/usr/bin/env python3
"""model_eval_report.py

## NAME

model_eval_report — generate a simple evaluation report for predictions (classification or regression)

## SYNOPSIS

Regression:
python model_eval_report.py --task regression --y-true y_true.csv --y-pred y_pred.csv --out out/

Classification:
python model_eval_report.py --task classification --y-true y_true.csv --y-pred y_pred.csv --out out/

## DESCRIPTION

This script reads two one-column CSV files (y_true and y_pred) and computes a
small set of common metrics.

Regression metrics:
- MAE, MSE, RMSE, R^2

Classification metrics:
- accuracy
- per-class precision/recall/F1 (from sklearn's classification_report)
- confusion matrix

Outputs:
- JSON report
- Markdown report

Implementation notes:
- Uses scikit-learn for metrics (commonly available in DS environments).
- Inputs are simple CSVs to keep the tool beginner-friendly.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_single_column_csv(path: Path, *, encoding: str = "utf-8", delimiter: str = ",") -> list[str]:
    with path.open("r", encoding=encoding, newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        rows = list(reader)

    if not rows:
        return []

    # If header-like (non-numeric) in first row and more than one row, treat it as header.
    # We keep it intentionally simple: if it has 1 cell and there are >1 rows, assume header.
    start = 1 if len(rows[0]) == 1 and len(rows) > 1 else 0

    out: list[str] = []
    for r in rows[start:]:
        if not r:
            continue
        out.append(r[0].strip())
    return out


def _to_float_list(values: list[str]) -> list[float]:
    out: list[float] = []
    for i, s in enumerate(values, start=1):
        try:
            out.append(float(s))
        except Exception as e:
            raise ValueError(f"Could not parse float on row {i}: {s!r}") from e
    return out


def evaluate_regression(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)} y_pred={len(y_pred)}")

    yt = _to_float_list(y_true)
    yp = _to_float_list(y_pred)

    # Import lazily to keep import-time side effects minimal.
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    mae = float(mean_absolute_error(yt, yp))
    mse = float(mean_squared_error(yt, yp))
    rmse = float(math.sqrt(mse))
    r2 = float(r2_score(yt, yp))

    return {"n": len(yt), "mae": mae, "mse": mse, "rmse": rmse, "r2": r2}


def evaluate_classification(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)} y_pred={len(y_pred)}")

    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

    acc = float(accuracy_score(y_true, y_pred))
    cm = confusion_matrix(y_true, y_pred)
    labels = sorted(set(y_true) | set(y_pred))

    report_dict = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    return {
        "n": len(y_true),
        "accuracy": acc,
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "classification_report": report_dict,
    }


def _render_markdown(report: dict) -> str:
    task = report.get("task")
    lines: list[str] = []
    lines.append("# Model Evaluation Report")
    lines.append("")
    lines.append(f"Generated: `{report.get('generated_at_utc', '')}`")
    lines.append(f"Task: `{task}`")
    lines.append("")

    metrics = report.get("metrics", {})

    lines.append("## Metrics")
    lines.append("")

    if task == "regression":
        for k in ("n", "mae", "mse", "rmse", "r2"):
            lines.append(f"- **{k}**: {metrics.get(k)}")

    elif task == "classification":
        lines.append(f"- **n**: {metrics.get('n')}")
        lines.append(f"- **accuracy**: {metrics.get('accuracy')}")
        lines.append("")

        lines.append("## Confusion matrix")
        lines.append("")
        labels = metrics.get("labels", [])
        cm = metrics.get("confusion_matrix", [])

        if labels and cm:
            lines.append("| true\\pred | " + " | ".join(str(x) for x in labels) + " |")
            lines.append("|---|" + "|".join(["---"] * len(labels)) + "|")
            for i, row in enumerate(cm):
                lines.append("| " + str(labels[i]) + " | " + " | ".join(str(x) for x in row) + " |")

        lines.append("")
        lines.append("## Classification report")
        lines.append("")
        lines.append("(From scikit-learn's `classification_report`)")
        lines.append("")

        cr = metrics.get("classification_report", {})
        # Render top-level scalar entries.
        for k, v in cr.items():
            if isinstance(v, dict):
                continue
            lines.append(f"- **{k}**: {v}")

    lines.append("")
    return "\n".join(lines)


def write_reports(report: dict, out_dir: Path, *, stem: str = "model_eval") -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    return {"json": json_path, "markdown": md_path}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate y_true vs y_pred and write JSON + Markdown reports")
    parser.add_argument("--task", choices=["classification", "regression"], required=True, help="Task type")
    parser.add_argument("--y-true", required=True, help="CSV with ground truth labels/values")
    parser.add_argument("--y-pred", required=True, help="CSV with predicted labels/values")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--encoding", default="utf-8", help="Text encoding")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter")
    parser.add_argument("--stem", default="model_eval", help="Output filename stem")

    args = parser.parse_args(argv)

    y_true_path = Path(args.y_true).resolve()
    y_pred_path = Path(args.y_pred).resolve()
    out_dir = Path(args.out).resolve()

    y_true = read_single_column_csv(y_true_path, encoding=args.encoding, delimiter=args.delimiter)
    y_pred = read_single_column_csv(y_pred_path, encoding=args.encoding, delimiter=args.delimiter)

    if args.task == "regression":
        metrics = evaluate_regression(y_true, y_pred)
    else:
        metrics = evaluate_classification(y_true, y_pred)

    report = {
        "generated_at_utc": utc_now_iso(),
        "task": args.task,
        "inputs": {"y_true": str(y_true_path), "y_pred": str(y_pred_path)},
        "metrics": metrics,
    }

    paths = write_reports(report, out_dir, stem=args.stem)
    print(f"Wrote: {paths['json']}")
    print(f"Wrote: {paths['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
