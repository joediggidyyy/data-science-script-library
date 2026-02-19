from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import scripts_root


pytestmark = pytest.mark.skipif(importlib.util.find_spec("sklearn") is None, reason="scikit-learn not installed")


def _make_dataset(tmp_path: Path) -> Path:
    build = scripts_root() / "data" / "build_feature_dataset.py"
    inp = tmp_path / "input.jsonl"
    out = tmp_path / "dataset"
    inp.write_text(
        '{"record_id":"r1","type":"post","content_length":10,"f_toxicity":0,"tv_id":"A"}\n'
        '{"record_id":"r2","type":"post","content_length":11,"f_toxicity":0,"tv_id":"A"}\n'
        '{"record_id":"r3","type":"post","content_length":40,"f_toxicity":1,"tv_id":"B"}\n'
        '{"record_id":"r4","type":"post","content_length":42,"f_toxicity":1,"tv_id":"B"}\n',
        encoding="utf-8",
    )
    res = subprocess.run([sys.executable, str(build), "--input", str(inp), "--out-dir", str(out)], cwd=str(tmp_path), capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return out / "dataset_manifest.json"


def test_train_sklearn_model_unsupervised(tmp_path: Path) -> None:
    script = scripts_root() / "ml" / "train_sklearn_model.py"
    dataset_manifest = _make_dataset(tmp_path)
    out = tmp_path / "model"
    res = subprocess.run(
        [sys.executable, str(script), "--dataset", str(dataset_manifest), "--out-dir", str(out), "--model-type", "unsupervised"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert (out / "model.joblib").exists()
    assert (out / "train_manifest.json").exists()
