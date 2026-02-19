from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import scripts_root


pytestmark = pytest.mark.skipif(importlib.util.find_spec("sklearn") is None, reason="scikit-learn not installed")


def test_score_unsupervised_model_outputs_csv(tmp_path: Path) -> None:
    build = scripts_root() / "data" / "build_feature_dataset.py"
    train = scripts_root() / "ml" / "train_sklearn_model.py"
    score = scripts_root() / "ml" / "score_unsupervised_model.py"

    inp = tmp_path / "input.jsonl"
    inp.write_text(
        '{"record_id":"r1","type":"post","content_length":10,"f_toxicity":0}\n'
        '{"record_id":"r2","type":"post","content_length":40,"f_toxicity":1}\n',
        encoding="utf-8",
    )

    ds_dir = tmp_path / "dataset"
    model_dir = tmp_path / "model"
    out_csv = tmp_path / "scores" / "scores.csv"

    r1 = subprocess.run([sys.executable, str(build), "--input", str(inp), "--out-dir", str(ds_dir)], cwd=str(tmp_path), capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr

    r2 = subprocess.run([sys.executable, str(train), "--dataset", str(ds_dir / "dataset_manifest.json"), "--out-dir", str(model_dir), "--model-type", "unsupervised"], cwd=str(tmp_path), capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr

    r3 = subprocess.run([sys.executable, str(score), "--dataset", str(ds_dir / "dataset_manifest.json"), "--model", str(model_dir / "train_manifest.json"), "--out-file", str(out_csv)], cwd=str(tmp_path), capture_output=True, text=True)
    assert r3.returncode == 0, r3.stderr
    assert out_csv.exists()
