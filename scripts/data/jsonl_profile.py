#!/usr/bin/env python3
"""jsonl_profile.py

## NAME

jsonl_profile — profile a JSONL file (schema inference + field frequency + examples)

## SYNOPSIS

python jsonl_profile.py <in_jsonl> --out <out_dir> [--max-records N] [--max-examples N]

## DESCRIPTION

This script reads newline-delimited JSON (JSONL) and produces a lightweight
profile report:

- total records
- parse errors / non-object records
- per-field presence count
- per-field null count
- per-field observed JSON types
- a few example values per field

It is designed to work in a streaming fashion (no pandas required) and to be
safe to run on large-ish logs.

Outputs:
- JSON report
- Markdown report

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def iter_jsonl(path: Path, *, encoding: str = "utf-8", max_records: Optional[int] = None) -> Iterator[tuple[int, Any]]:
    """Yield (line_no, parsed_json) for each non-empty line."""

    with path.open("r", encoding=encoding) as fh:
        for line_no, line in enumerate(fh, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                yield line_no, json.loads(s)
            except json.JSONDecodeError as e:
                yield line_no, e

            if max_records is not None and max_records > 0:
                max_records -= 1
                if max_records <= 0:
                    break


@dataclass
class FieldProfile:
    present: int = 0
    nulls: int = 0
    types: Counter[str] = None  # type: ignore[assignment]
    examples: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.types is None:
            self.types = Counter()
        if self.examples is None:
            self.examples = []


def _to_example_str(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return repr(value)


def profile_jsonl(
    path: Path,
    *,
    encoding: str = "utf-8",
    max_records: Optional[int] = None,
    max_examples: int = 3,
) -> dict:
    """Profile a JSONL file; returns a JSON-serializable dict."""

    fields: dict[str, FieldProfile] = {}

    total_lines = 0
    total_records = 0
    parse_errors = 0
    non_object_records = 0

    for line_no, parsed in iter_jsonl(path, encoding=encoding, max_records=max_records):
        total_lines += 1

        if isinstance(parsed, json.JSONDecodeError):
            parse_errors += 1
            continue

        if not isinstance(parsed, dict):
            non_object_records += 1
            continue

        total_records += 1

        for k, v in parsed.items():
            fp = fields.get(k)
            if fp is None:
                fp = FieldProfile()
                fields[k] = fp

            fp.present += 1
            if v is None:
                fp.nulls += 1
            fp.types[_json_type(v)] += 1

            if len(fp.examples) < max_examples:
                ex = _to_example_str(v)
                # avoid duplicates to keep examples diverse
                if ex not in fp.examples:
                    fp.examples.append(ex)

    report = {
        "generated_at_utc": utc_now_iso(),
        "input": {"path": str(path), "encoding": encoding, "max_records": max_records},
        "summary": {
            "total_lines_processed": total_lines,
            "total_object_records": total_records,
            "parse_errors": parse_errors,
            "non_object_records": non_object_records,
            "unique_fields": len(fields),
        },
        "fields": {
            k: {
                "present": fp.present,
                "nulls": fp.nulls,
                "types": dict(fp.types),
                "examples": fp.examples,
            }
            for k, fp in sorted(fields.items(), key=lambda kv: kv[0])
        },
    }

    return report


def _render_markdown(report: dict) -> str:
    summary = report.get("summary", {})
    fields = report.get("fields", {})

    lines: list[str] = []
    lines.append("# JSONL Profile Report")
    lines.append("")
    lines.append(f"Generated: `{report.get('generated_at_utc', '')}`")
    lines.append(f"Input: `{report.get('input', {}).get('path', '')}`")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    for k in (
        "total_lines_processed",
        "total_object_records",
        "parse_errors",
        "non_object_records",
        "unique_fields",
    ):
        lines.append(f"- **{k}**: {summary.get(k, 0)}")

    lines.append("")
    lines.append("## Fields")
    lines.append("")
    lines.append("| field | present | nulls | types | examples |")
    lines.append("|---|---:|---:|---|---|")

    for name, fp in fields.items():
        types = fp.get("types", {})
        types_s = ", ".join(f"{t}:{n}" for t, n in sorted(types.items(), key=lambda kv: kv[0]))
        examples = fp.get("examples", [])
        ex_s = "; ".join(str(x) for x in examples)
        lines.append(f"| `{name}` | {fp.get('present', 0)} | {fp.get('nulls', 0)} | {types_s} | {ex_s} |")

    lines.append("")
    return "\n".join(lines)


def write_reports(report: dict, out_dir: Path, *, stem: str = "jsonl_profile") -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    return {"json": json_path, "markdown": md_path}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Profile a JSONL file and emit JSON + Markdown reports")
    parser.add_argument("in_jsonl", help="Input JSONL file")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--encoding", default="utf-8", help="Text encoding (default: utf-8)")
    parser.add_argument("--max-records", type=int, default=0, help="Max records to process (0 = no limit)")
    parser.add_argument("--max-examples", type=int, default=3, help="Max example values per field")
    parser.add_argument("--stem", default="jsonl_profile", help="Output filename stem")

    args = parser.parse_args(argv)

    in_path = Path(args.in_jsonl).resolve()
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    max_records = None if args.max_records == 0 else args.max_records

    report = profile_jsonl(
        in_path,
        encoding=args.encoding,
        max_records=max_records,
        max_examples=args.max_examples,
    )

    out_dir = Path(args.out).resolve()
    paths = write_reports(report, out_dir, stem=args.stem)

    print(f"Wrote: {paths['json']}")
    print(f"Wrote: {paths['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
