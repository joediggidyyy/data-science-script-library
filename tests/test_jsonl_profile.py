from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_profile_jsonl_counts_fields_and_types(tmp_path: Path) -> None:
    mod = import_module_from_path(
        "jsonl_profile",
        scripts_root() / "data" / "jsonl_profile.py",
    )

    p = tmp_path / "in.jsonl"
    p.write_text(
        "\n".join(
            [
                json.dumps({"a": 1, "b": "x", "c": None}),
                "{not-json}",
                json.dumps([1, 2, 3]),
                json.dumps({"a": 2.5, "b": "y"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.profile_jsonl(p)
    s = report["summary"]

    assert s["parse_errors"] == 1
    assert s["non_object_records"] == 1
    assert s["total_object_records"] == 2

    fields = report["fields"]
    assert fields["a"]["present"] == 2
    assert fields["a"]["types"].get("number", 0) == 2

    assert fields["c"]["present"] == 1
    assert fields["c"]["nulls"] == 1
    assert fields["c"]["types"].get("null", 0) == 1


def test_jsonl_profile_cli_writes_reports(tmp_path: Path) -> None:
    script = scripts_root() / "data" / "jsonl_profile.py"

    in_path = tmp_path / "in.jsonl"
    out_dir = tmp_path / "out"

    in_path.write_text(json.dumps({"x": 1}) + "\n" + json.dumps({"x": 2, "y": "z"}) + "\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(script),
            str(in_path),
            "--out",
            str(out_dir),
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr

    assert (out_dir / "jsonl_profile.json").exists()
    assert (out_dir / "jsonl_profile.md").exists()
