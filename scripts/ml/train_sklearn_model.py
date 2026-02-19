"""Train sklearn models from dataset artifacts.

Supported model types:
- supervised: RandomForestClassifier (requires labels)
- unsupervised: IsolationForest
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import joblib
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score
except Exception:
    print("Error: scikit-learn and joblib are required.")
    sys.exit(1)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_dataset(manifest_path: Path) -> Tuple[List[Dict[str, str]], Dict[str, str], Dict[str, str], List[str]]:
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    features = _read_csv(Path(m["features_csv"]))
    splits = {r["record_id"]: r["split"] for r in _read_csv(Path(m["splits_csv"]))}
    labels: Dict[str, str] = {}
    if m.get("labels_csv"):
        labels = {r["record_id"]: (r.get("label") or "") for r in _read_csv(Path(m["labels_csv"]))}
    feature_cols = [c for c in list(m.get("feature_columns") or []) if c != "record_id"]
    return features, splits, labels, feature_cols


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Train sklearn model from dataset manifest.")
    ap.add_argument("--dataset", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--model-type", choices=["supervised", "unsupervised"], default="supervised")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)

    features, splits, labels, cols = _load_dataset(args.dataset)
    if not cols:
        print("Error: no feature columns available")
        return 2

    x_train: List[List[float]] = []
    y_train: List[str] = []
    x_val: List[List[float]] = []
    y_val: List[str] = []

    for r in features:
        rid = str(r.get("record_id") or "")
        split = splits.get(rid, "train")
        vec = []
        for c in cols:
            try:
                vec.append(float(r.get(c, 0.0)))
            except Exception:
                vec.append(0.0)

        if split == "train":
            x_train.append(vec)
            if rid in labels:
                y_train.append(labels[rid])
        elif split == "val":
            x_val.append(vec)
            if rid in labels:
                y_val.append(labels[rid])

    args.out_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.out_dir / "model.joblib"
    metrics_path = args.out_dir / "metrics.json"
    manifest_path = args.out_dir / "train_manifest.json"

    metrics: Dict[str, Any] = {}
    if args.model_type == "supervised":
        if len(y_train) != len(x_train):
            print("Error: supervised mode requires labels for all training rows")
            return 2
        model = RandomForestClassifier(n_estimators=100, random_state=int(args.seed))
        model.fit(x_train, y_train)
        if x_val and len(y_val) == len(x_val):
            pred = model.predict(x_val)
            metrics["accuracy"] = float(accuracy_score(y_val, pred))
            metrics["f1_macro"] = float(f1_score(y_val, pred, average="macro"))
    else:
        model = IsolationForest(n_estimators=100, random_state=int(args.seed), contamination=0.1)
        model.fit(x_train)
        metrics["trained_rows"] = len(x_train)

    joblib.dump(model, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")

    train_manifest = {
        "created_at_utc": _utc_now_iso(),
        "dataset_manifest": str(args.dataset),
        "model_type": str(args.model_type),
        "model_path": str(model_path),
        "metrics_path": str(metrics_path),
        "feature_columns": cols,
        "seed": int(args.seed),
    }
    manifest_path.write_text(json.dumps(train_manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote: {model_path}")
    print(f"Wrote: {metrics_path}")
    print(f"Wrote: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
