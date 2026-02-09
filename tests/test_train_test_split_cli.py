from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_split_indices_stratified_is_deterministic() -> None:
    mod = import_module_from_path(
        "train_test_split_cli",
        scripts_root() / "ml" / "train_test_split_cli.py",
    )

    labels = ["A"] * 8 + ["B"] * 2
    r1 = mod.split_indices(10, test_size=0.2, seed=123, stratify=labels)
    r2 = mod.split_indices(10, test_size=0.2, seed=123, stratify=labels)

    assert r1 == r2
    assert len(r1.test_indices) == 2
    # should include at least one from each class if possible at this size
    test_labels = {labels[i] for i in r1.test_indices}
    assert test_labels.issubset({"A", "B"})


def test_cli_writes_train_test_and_indices(tmp_path: Path) -> None:
    script = scripts_root() / "ml" / "train_test_split_cli.py"

    in_csv = tmp_path / "in.csv"
    out_dir = tmp_path / "out"

    # 10 rows with imbalanced classes
    lines = ["x,label"]
    for i in range(8):
        lines.append(f"{i},A")
    for i in range(8, 10):
        lines.append(f"{i},B")
    in_csv.write_text("\n".join(lines) + "\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            str(in_csv),
            "--out",
            str(out_dir),
            "--test-size",
            "0.2",
            "--seed",
            "123",
            "--stratify-col",
            "label",
            "--write-indices",
            "--preserve-order",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr

    train_path = out_dir / "train.csv"
    test_path = out_dir / "test.csv"
    idx_path = out_dir / "split_indices.json"

    assert train_path.exists()
    assert test_path.exists()
    assert idx_path.exists()

    train_rows = _read_csv_rows(train_path)
    test_rows = _read_csv_rows(test_path)

    assert len(train_rows) + len(test_rows) == 10
    assert len(test_rows) == 2

    payload = json.loads(idx_path.read_text(encoding="utf-8"))
    assert len(payload["train_indices"]) == len(train_rows)
    assert len(payload["test_indices"]) == len(test_rows)

    # Ensure indices are disjoint
    assert set(payload["train_indices"]).isdisjoint(set(payload["test_indices"]))
