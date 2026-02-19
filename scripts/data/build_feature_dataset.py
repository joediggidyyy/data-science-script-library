"""Build a feature dataset from JSONL telemetry-like records.

Outputs:
- features.csv
- labels.csv (optional)
- splits.csv
- dataset_manifest.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _stable_record_id(rec: Dict[str, Any]) -> str:
    raw = json.dumps(rec, sort_keys=True, ensure_ascii=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _split_bucket(record_id: str, seed: int) -> float:
    h = hashlib.sha256(f"{seed}:{record_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) / float(0xFFFFFFFF)


def _assign_split(bucket: float, train: float, val: float, test: float) -> str:
    s = train + val + test
    if s <= 0:
        return "train"
    train, val, test = train / s, val / s, test / s
    if bucket < train:
        return "train"
    if bucket < (train + val):
        return "val"
    return "test"


def _extract_features(rec: Dict[str, Any]) -> Dict[str, Any]:
    t = str(rec.get("type") or rec.get("event_type") or "unknown").strip().lower()
    row = {
        "record_id": str(rec.get("record_id") or _stable_record_id(rec)),
        "ts_epoch": _safe_float(rec.get("f_timestamp_epoch") or rec.get("ts_epoch") or 0.0),
        "content_length": _safe_int(rec.get("content_length"), 0),
        "has_code_block": 1 if bool(rec.get("has_code_block")) else 0,
        "has_link": 1 if bool(rec.get("has_link")) else 0,
        "tags_count": _safe_int(rec.get("tags_count"), 0),
        "mentions_count": _safe_int(rec.get("mentions_count"), 0),
        "f_complexity": _safe_float(rec.get("f_complexity"), 0.0),
        "f_code_density": _safe_float(rec.get("f_code_density"), 0.0),
        "f_toxicity": _safe_int(rec.get("f_toxicity"), 0),
        "type_post": 1 if t == "post" else 0,
        "type_reply": 1 if t == "reply" else 0,
        "type_repost": 1 if t == "repost" else 0,
        "type_dm": 1 if t == "dm" else 0,
        "type_follow": 1 if t == "follow" else 0,
        "type_mention": 1 if t == "mention" else 0,
        "type_unknown": 1 if t not in {"post", "reply", "repost", "dm", "follow", "mention"} else 0,
    }
    return row


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build feature datasets from JSONL records.")
    ap.add_argument("--input", action="append", required=True, type=Path, help="Input JSONL path (repeatable)")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--split-train", type=float, default=0.7)
    ap.add_argument("--split-val", type=float, default=0.15)
    ap.add_argument("--split-test", type=float, default=0.15)
    ap.add_argument("--label-key", default="tv_id", help="Optional label field key in records")
    args = ap.parse_args(argv)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    features_path = out_dir / "features.csv"
    labels_path = out_dir / "labels.csv"
    splits_path = out_dir / "splits.csv"
    manifest_path = out_dir / "dataset_manifest.json"

    rows: List[Dict[str, Any]] = []
    labels: List[Dict[str, str]] = []
    for p in args.input:
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    continue
                if not isinstance(rec, dict):
                    continue
                row = _extract_features(rec)
                rows.append(row)
                lbl = rec.get(args.label_key)
                if isinstance(lbl, str) and lbl:
                    labels.append({"record_id": row["record_id"], "label": lbl})

    if not rows:
        print("Error: no valid records found")
        return 2

    cols = list(rows[0].keys())
    with features_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    if labels:
        with labels_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["record_id", "label"])
            w.writeheader()
            for r in labels:
                w.writerow(r)

    split_counts = {"train": 0, "val": 0, "test": 0}
    with splits_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["record_id", "split"])
        w.writeheader()
        for r in sorted(rows, key=lambda x: x["record_id"]):
            b = _split_bucket(str(r["record_id"]), int(args.seed))
            s = _assign_split(b, float(args.split_train), float(args.split_val), float(args.split_test))
            split_counts[s] += 1
            w.writerow({"record_id": r["record_id"], "split": s})

    manifest = {
        "created_at_utc": _utc_now_iso(),
        "inputs": [str(p) for p in args.input],
        "features_csv": str(features_path),
        "labels_csv": str(labels_path) if labels else "",
        "splits_csv": str(splits_path),
        "feature_columns": cols,
        "total_records": len(rows),
        "has_labels": bool(labels),
        "seed": int(args.seed),
        "split": {"train": float(args.split_train), "val": float(args.split_val), "test": float(args.split_test)},
        "split_counts": split_counts,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote: {features_path}")
    if labels:
        print(f"Wrote: {labels_path}")
    print(f"Wrote: {splits_path}")
    print(f"Wrote: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
