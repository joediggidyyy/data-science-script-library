from __future__ import annotations

import csv
import json
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_jsonl_to_csv_infers_fields_and_writes_csv(tmp_path: Path) -> None:
    mod = import_module_from_path(
        "jsonl_to_csv",
        scripts_root() / "data" / "jsonl_to_csv.py",
    )

    in_path = tmp_path / "in.jsonl"
    out_path = tmp_path / "out.csv"

    in_path.write_text(
        "\n".join(
            [
                json.dumps({"a": 1, "b": {"x": 2}}),
                json.dumps({"b": 3, "c": 4}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    count = mod.jsonl_to_csv(in_path, out_path)
    assert count == 2
    assert out_path.exists()

    rows = list(csv.DictReader(out_path.open("r", encoding="utf-8", newline="")))
    assert len(rows) == 2

    # Field order should be stable by first-seen: a, b, c
    assert rows[0].get("a") == "1"
    assert rows[0].get("c") in (None, "")

    # Nested dict should be serialized as JSON string (not lost)
    b0 = rows[0].get("b")
    assert b0 is not None and b0 != ""
    assert json.loads(b0) == {"x": 2}


def test_jsonl_to_csv_respects_explicit_fields(tmp_path: Path) -> None:
    mod = import_module_from_path(
        "jsonl_to_csv_explicit",
        scripts_root() / "data" / "jsonl_to_csv.py",
    )

    in_path = tmp_path / "in.jsonl"
    out_path = tmp_path / "out.csv"

    in_path.write_text(json.dumps({"a": 1, "b": 2}) + "\n", encoding="utf-8")

    count = mod.jsonl_to_csv(in_path, out_path, fields=["b", "a"])
    assert count == 1

    header = out_path.read_text(encoding="utf-8").splitlines()[0]
    assert header == "b,a"
