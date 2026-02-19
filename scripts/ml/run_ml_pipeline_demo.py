"""Run a small synthetic end-to-end ML pipeline demo.

Steps:
1) Generate synthetic JSONL records
2) Build dataset
3) Train model
4) Score records
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _generate_jsonl(path: Path, n_normal: int, n_anomaly: int, seed: int) -> None:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for i in range(n_normal):
            rec = {
                "record_id": f"normal_{i}",
                "type": "post",
                "content_length": rng.randint(20, 60),
                "has_code_block": False,
                "has_link": rng.random() < 0.1,
                "tags_count": rng.randint(0, 2),
                "mentions_count": rng.randint(0, 2),
                "f_complexity": rng.random() * 0.3,
                "f_code_density": rng.random() * 0.2,
                "f_toxicity": 0,
                "tv_id": "TV-0",
            }
            f.write(json.dumps(rec) + "\n")
        for i in range(n_anomaly):
            rec = {
                "record_id": f"anomaly_{i}",
                "type": "post",
                "content_length": rng.randint(120, 300),
                "has_code_block": True,
                "has_link": True,
                "tags_count": rng.randint(3, 8),
                "mentions_count": rng.randint(3, 12),
                "f_complexity": 0.7 + rng.random() * 0.3,
                "f_code_density": 0.6 + rng.random() * 0.4,
                "f_toxicity": 1,
                "tv_id": "TV-3",
            }
            f.write(json.dumps(rec) + "\n")


def _run(cmd: list[str], cwd: Path) -> int:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
    return int(p.returncode)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Run synthetic ML pipeline demo.")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--normal", type=int, default=50)
    ap.add_argument("--anomaly", type=int, default=10)
    args = ap.parse_args(argv)

    root = args.out_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)

    inp = root / "input" / "telemetry.jsonl"
    ds = root / "dataset"
    model = root / "model"
    scores = root / "scores" / "scores.csv"

    _generate_jsonl(inp, int(args.normal), int(args.anomaly), int(args.seed))

    scripts_dir = Path(__file__).resolve().parents[1]
    py = sys.executable

    c1 = [py, str(scripts_dir / "data" / "build_feature_dataset.py"), "--input", str(inp), "--out-dir", str(ds), "--seed", str(args.seed)]
    if _run(c1, cwd=root) != 0:
        return 2

    c2 = [py, str(scripts_dir / "ml" / "train_sklearn_model.py"), "--dataset", str(ds / "dataset_manifest.json"), "--out-dir", str(model), "--model-type", "unsupervised", "--seed", str(args.seed)]
    if _run(c2, cwd=root) != 0:
        return 2

    c3 = [py, str(scripts_dir / "ml" / "score_unsupervised_model.py"), "--dataset", str(ds / "dataset_manifest.json"), "--model", str(model / "train_manifest.json"), "--out-file", str(scores)]
    if _run(c3, cwd=root) != 0:
        return 2

    print(f"Pipeline demo complete under: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
