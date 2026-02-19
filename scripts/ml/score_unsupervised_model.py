"""Score records using a trained unsupervised sklearn model.

Expected model API: decision_function(X).
Outputs CSV with columns: record_id,score_raw
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import joblib
except Exception:
    print("Error: joblib is required.")
    sys.exit(1)


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_model_path(model_arg: Path) -> Path:
    if model_arg.suffix.lower() == ".json":
        payload = json.loads(model_arg.read_text(encoding="utf-8"))
        p = payload.get("model_path")
        if not isinstance(p, str) or not p:
            raise ValueError("train manifest missing model_path")
        return Path(p)
    return model_arg


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Score dataset records using an unsupervised model.")
    ap.add_argument("--dataset", required=True, type=Path, help="Path to dataset_manifest.json")
    ap.add_argument("--model", required=True, type=Path, help="Path to model.joblib or train_manifest.json")
    ap.add_argument("--out-file", required=True, type=Path)
    args = ap.parse_args(argv)

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    feature_cols = [c for c in list(dataset.get("feature_columns") or []) if c != "record_id"]
    if not feature_cols:
        print("Error: dataset feature_columns missing")
        return 2

    feature_rows = _read_csv(Path(dataset["features_csv"]))
    model_path = _load_model_path(args.model)
    model = joblib.load(model_path)

    x: List[List[float]] = []
    ids: List[str] = []
    for r in feature_rows:
        ids.append(str(r.get("record_id") or ""))
        vec = []
        for c in feature_cols:
            try:
                vec.append(float(r.get(c, 0.0)))
            except Exception:
                vec.append(0.0)
        x.append(vec)

    if not hasattr(model, "decision_function"):
        print("Error: model does not expose decision_function")
        return 2

    scores = model.decision_function(x)
    args.out_file.parent.mkdir(parents=True, exist_ok=True)
    with args.out_file.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["record_id", "score_raw"])
        for rid, s in zip(ids, scores):
            w.writerow([rid, float(s)])

    print(f"Wrote: {args.out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
