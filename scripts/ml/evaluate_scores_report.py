"""Evaluate score thresholds and emit JSON + Markdown reports.

Supports labeled and unlabeled modes:
- Labeled: selects threshold maximizing F1 under max-FPR constraint.
- Unlabeled: selects quantile threshold to flag approximately max-FPR records.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _confusion(y_true: List[int], y_pred: List[int]) -> Dict[str, int]:
    tp = fp = tn = fn = 0
    for t, p in zip(y_true, y_pred):
        if t == 1 and p == 1:
            tp += 1
        elif t == 0 and p == 1:
            fp += 1
        elif t == 0 and p == 0:
            tn += 1
        elif t == 1 and p == 0:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def _metrics(conf: Dict[str, int]) -> Dict[str, float]:
    tp = float(conf.get("tp", 0))
    fp = float(conf.get("fp", 0))
    tn = float(conf.get("tn", 0))
    fn = float(conf.get("fn", 0))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "fpr": fpr}


def _choose_threshold(scores: List[float], y_true: List[int], max_fpr: float) -> float:
    if not scores:
        return 0.0
    candidates = sorted(set(scores))
    best_thr = candidates[0]
    best_f1 = -1.0
    for thr in candidates:
        y_pred = [1 if s >= thr else 0 for s in scores]
        m = _metrics(_confusion(y_true, y_pred))
        if m["fpr"] <= max_fpr and m["f1"] >= best_f1:
            best_f1 = m["f1"]
            best_thr = thr
    return float(best_thr)


@dataclass
class EvalResult:
    threshold: float
    max_fpr: float
    has_labels: bool
    counts: Dict[str, int]
    metrics: Dict[str, float]


def evaluate_scores(
    scores_csv: Path,
    *,
    score_col: str,
    id_col: str,
    labels_csv: Optional[Path],
    label_col: str,
    positive_label: str,
    max_fpr: float,
) -> EvalResult:
    rows = _read_csv(scores_csv)
    scores: List[float] = []
    ids: List[str] = []
    for row in rows:
        try:
            scores.append(float(row[score_col]))
            ids.append(str(row.get(id_col, "")).strip())
        except Exception:
            continue

    label_map: Dict[str, str] = {}
    if labels_csv is not None and labels_csv.exists():
        for row in _read_csv(labels_csv):
            rid = str(row.get(id_col, "")).strip()
            lbl = str(row.get(label_col, "")).strip()
            if rid:
                label_map[rid] = lbl

    if label_map:
        y_true = [1 if label_map.get(rid) == positive_label else 0 for rid in ids]
        thr = _choose_threshold(scores, y_true, max_fpr=max_fpr)
        y_pred = [1 if s >= thr else 0 for s in scores]
        conf = _confusion(y_true, y_pred)
        return EvalResult(
            threshold=float(thr),
            max_fpr=float(max_fpr),
            has_labels=True,
            counts=conf,
            metrics=_metrics(conf),
        )

    if not scores:
        thr = 0.0
        flagged = 0
    else:
        srt = sorted(scores)
        idx = int(max(0, min(len(srt) - 1, round((1.0 - max_fpr) * (len(srt) - 1)))))
        thr = float(srt[idx])
        flagged = sum(1 for s in scores if s >= thr)

    total = len(scores)
    return EvalResult(
        threshold=float(thr),
        max_fpr=float(max_fpr),
        has_labels=False,
        counts={"flagged": int(flagged), "total": int(total)},
        metrics={"flag_rate": (float(flagged) / float(total)) if total else 0.0},
    )


def _render_markdown(result: EvalResult, run_id: str, inputs: Dict[str, str]) -> str:
    lines = [
        "# Score Evaluation Report",
        "",
        f"- Created (UTC): {_utc_now_iso()}",
        f"- Run ID: {run_id}",
        f"- Labeled mode: {'yes' if result.has_labels else 'no'}",
        f"- Max FPR: {result.max_fpr}",
        f"- Threshold: {result.threshold}",
        "",
        "## Inputs",
        "",
        f"- scores_csv: `{inputs['scores_csv']}`",
        f"- labels_csv: `{inputs['labels_csv']}`",
        "",
        "## Metrics",
        "",
    ]
    for k, v in sorted(result.metrics.items()):
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Counts", ""])
    for k, v in sorted(result.counts.items()):
        lines.append(f"- {k}: {v}")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate score thresholds and write report artifacts.")
    ap.add_argument("--scores-csv", required=True, type=Path)
    ap.add_argument("--score-col", default="score")
    ap.add_argument("--id-col", default="record_id")
    ap.add_argument("--labels-csv", type=Path, default=None)
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--positive-label", default="1")
    ap.add_argument("--max-fpr", type=float, default=0.01)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args(argv)

    result = evaluate_scores(
        args.scores_csv,
        score_col=str(args.score_col),
        id_col=str(args.id_col),
        labels_csv=args.labels_csv,
        label_col=str(args.label_col),
        positive_label=str(args.positive_label),
        max_fpr=float(args.max_fpr),
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(args.run_id) if args.run_id else args.out_dir.name
    payload = {
        "created_at_utc": _utc_now_iso(),
        "run_id": run_id,
        "inputs": {
            "scores_csv": str(args.scores_csv),
            "labels_csv": str(args.labels_csv) if args.labels_csv else "",
            "score_col": str(args.score_col),
            "id_col": str(args.id_col),
            "label_col": str(args.label_col),
            "positive_label": str(args.positive_label),
        },
        "result": asdict(result),
    }

    json_path = args.out_dir / "score_eval_report.json"
    md_path = args.out_dir / "score_eval_report.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown(result, run_id, payload["inputs"]), encoding="utf-8")

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
