#!/usr/bin/env python3
"""csv_profile_report.py

## NAME

csv_profile_report — quick CSV dataset summary (nulls, uniques, numeric stats, sample rows)

## SYNOPSIS

python csv_profile_report.py <in_csv> --out <out_dir> [--delimiter ,] [--max-rows N]

## DESCRIPTION

This script reads a CSV file and produces a lightweight profile report suitable
for quick QA and classroom work:

- row/column counts
- per-column missing counts (empty string)
- per-column unique counts (capped to avoid memory blowups)
- per-column numeric stats when values parse as floats (min/max/mean)
- a small sample of the first rows

Outputs:
- Markdown report
- HTML report

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import csv
import html
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class NumericStats:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    min: float = math.inf
    max: float = -math.inf

    def add(self, x: float) -> None:
        self.count += 1
        if x < self.min:
            self.min = x
        if x > self.max:
            self.max = x

        # Welford
        delta = x - self.mean
        self.mean += delta / self.count
        delta2 = x - self.mean
        self.m2 += delta * delta2


@dataclass
class ColumnProfile:
    missing: int = 0
    nonempty: int = 0
    unique_capped: bool = False
    unique_values: set[str] = None  # type: ignore[assignment]
    examples: list[str] = None  # type: ignore[assignment]
    numeric: NumericStats = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.unique_values is None:
            self.unique_values = set()
        if self.examples is None:
            self.examples = []
        if self.numeric is None:
            self.numeric = NumericStats()


def _try_float(s: str) -> Optional[float]:
    try:
        x = float(s)
    except Exception:
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def profile_csv(
    path: Path,
    *,
    encoding: str = "utf-8",
    delimiter: str = ",",
    max_rows: int = 0,
    max_uniques: int = 50_000,
    max_examples: int = 5,
    sample_rows: int = 5,
) -> dict:
    """Profile a CSV file; returns a JSON-serializable dict."""

    with path.open("r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV appears to have no header row")

        cols = {name: ColumnProfile() for name in reader.fieldnames}

        rows_seen = 0
        samples: list[dict[str, str]] = []

        for row in reader:
            rows_seen += 1

            if sample_rows > 0 and len(samples) < sample_rows:
                samples.append({k: (row.get(k) or "") for k in cols.keys()})

            for name, prof in cols.items():
                raw = row.get(name)
                val = (raw or "").strip()

                if val == "":
                    prof.missing += 1
                    continue

                prof.nonempty += 1

                if not prof.unique_capped:
                    if len(prof.unique_values) < max_uniques:
                        prof.unique_values.add(val)
                    else:
                        prof.unique_capped = True
                        prof.unique_values.clear()

                if len(prof.examples) < max_examples and val not in prof.examples:
                    prof.examples.append(val)

                fx = _try_float(val)
                if fx is not None:
                    prof.numeric.add(fx)

            if max_rows and rows_seen >= max_rows:
                break

    report = {
        "generated_at_utc": utc_now_iso(),
        "input": {
            "path": str(path),
            "encoding": encoding,
            "delimiter": delimiter,
            "max_rows": max_rows,
        },
        "summary": {
            "rows_profiled": rows_seen,
            "columns": list(cols.keys()),
            "num_columns": len(cols),
        },
        "columns": {},
        "samples": samples,
    }

    for name, prof in cols.items():
        numeric = None
        if prof.numeric.count > 0:
            numeric = {
                "count": prof.numeric.count,
                "min": prof.numeric.min,
                "max": prof.numeric.max,
                "mean": prof.numeric.mean,
            }

        unique_count: Any
        if prof.unique_capped:
            unique_count = f">= {max_uniques} (capped)"
        else:
            unique_count = len(prof.unique_values)

        report["columns"][name] = {
            "missing": prof.missing,
            "nonempty": prof.nonempty,
            "unique": unique_count,
            "examples": prof.examples,
            "numeric": numeric,
        }

    return report


def _render_markdown(report: dict) -> str:
    s = report.get("summary", {})
    cols = report.get("columns", {})

    lines: list[str] = []
    lines.append("# CSV Profile Report")
    lines.append("")
    lines.append(f"Generated: `{report.get('generated_at_utc', '')}`")
    lines.append(f"Input: `{report.get('input', {}).get('path', '')}`")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **rows_profiled**: {s.get('rows_profiled', 0)}")
    lines.append(f"- **num_columns**: {s.get('num_columns', 0)}")
    lines.append("")

    lines.append("## Columns")
    lines.append("")
    lines.append("| column | missing | nonempty | uniques | numeric (min/max/mean) | examples |")
    lines.append("|---|---:|---:|---:|---|---|")

    for name, p in cols.items():
        numeric = p.get("numeric")
        if numeric:
            n_str = f"{numeric['min']:.6g} / {numeric['max']:.6g} / {numeric['mean']:.6g} (n={numeric['count']})"
        else:
            n_str = ""
        ex = "; ".join(str(x) for x in p.get("examples", []))
        lines.append(
            f"| `{name}` | {p.get('missing', 0)} | {p.get('nonempty', 0)} | {p.get('unique', 0)} | {n_str} | {ex} |"
        )

    samples = report.get("samples", [])
    if samples:
        lines.append("")
        lines.append("## Sample rows")
        lines.append("")
        header = list(samples[0].keys())
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for row in samples:
            lines.append("| " + " | ".join(str(row.get(h, "")) for h in header) + " |")

    lines.append("")
    return "\n".join(lines)


def _render_html(report: dict) -> str:
    s = report.get("summary", {})
    cols = report.get("columns", {})
    samples = report.get("samples", [])

    def esc(x: Any) -> str:
        return html.escape(str(x))

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append("<html><head><meta charset='utf-8'>")
    parts.append("<title>CSV Profile Report</title>")
    parts.append(
        "<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;} table{border-collapse:collapse;} th,td{border:1px solid #ddd;padding:6px 10px;} th{background:#f6f6f6;text-align:left;} code{background:#f2f2f2;padding:1px 4px;border-radius:4px;}</style>"
    )
    parts.append("</head><body>")

    parts.append("<h1>CSV Profile Report</h1>")
    parts.append(f"<p><strong>Generated</strong>: <code>{esc(report.get('generated_at_utc',''))}</code><br>")
    parts.append(f"<strong>Input</strong>: <code>{esc(report.get('input', {}).get('path',''))}</code></p>")

    parts.append("<h2>Summary</h2>")
    parts.append("<ul>")
    parts.append(f"<li><strong>rows_profiled</strong>: {esc(s.get('rows_profiled',0))}</li>")
    parts.append(f"<li><strong>num_columns</strong>: {esc(s.get('num_columns',0))}</li>")
    parts.append("</ul>")

    parts.append("<h2>Columns</h2>")
    parts.append("<table><thead><tr>")
    parts.append("<th>column</th><th>missing</th><th>nonempty</th><th>uniques</th><th>numeric (min/max/mean)</th><th>examples</th>")
    parts.append("</tr></thead><tbody>")
    for name, p in cols.items():
        numeric = p.get("numeric")
        if numeric:
            n_str = f"{numeric['min']:.6g} / {numeric['max']:.6g} / {numeric['mean']:.6g} (n={numeric['count']})"
        else:
            n_str = ""
        ex = "; ".join(str(x) for x in p.get("examples", []))
        parts.append("<tr>")
        parts.append(f"<td><code>{esc(name)}</code></td>")
        parts.append(f"<td>{esc(p.get('missing',0))}</td>")
        parts.append(f"<td>{esc(p.get('nonempty',0))}</td>")
        parts.append(f"<td>{esc(p.get('unique',0))}</td>")
        parts.append(f"<td>{esc(n_str)}</td>")
        parts.append(f"<td>{esc(ex)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")

    if samples:
        parts.append("<h2>Sample rows</h2>")
        header = list(samples[0].keys())
        parts.append("<table><thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in header) + "</tr></thead><tbody>")
        for row in samples:
            parts.append("<tr>" + "".join(f"<td>{esc(row.get(h,''))}</td>" for h in header) + "</tr>")
        parts.append("</tbody></table>")

    parts.append("</body></html>")
    return "\n".join(parts)


def write_reports(report: dict, out_dir: Path, *, stem: str = "csv_profile") -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"{stem}.md"
    html_path = out_dir / f"{stem}.html"

    md_path.write_text(_render_markdown(report), encoding="utf-8")
    html_path.write_text(_render_html(report), encoding="utf-8")

    return {"markdown": md_path, "html": html_path}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a quick CSV profile report (Markdown + HTML)")
    parser.add_argument("in_csv", help="Input CSV file")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--encoding", default="utf-8", help="Text encoding (default: utf-8)")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: ,)")
    parser.add_argument("--max-rows", type=int, default=0, help="Max rows to profile (0 = no limit)")
    parser.add_argument("--max-uniques", type=int, default=50_000, help="Cap unique tracking per column")
    parser.add_argument("--max-examples", type=int, default=5, help="Max example values per column")
    parser.add_argument("--sample-rows", type=int, default=5, help="Number of sample rows to include")
    parser.add_argument("--stem", default="csv_profile", help="Output filename stem")

    args = parser.parse_args(argv)

    in_path = Path(args.in_csv).resolve()
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    report = profile_csv(
        in_path,
        encoding=args.encoding,
        delimiter=args.delimiter,
        max_rows=args.max_rows,
        max_uniques=args.max_uniques,
        max_examples=args.max_examples,
        sample_rows=args.sample_rows,
    )

    out_dir = Path(args.out).resolve()
    paths = write_reports(report, out_dir, stem=args.stem)

    print(f"Wrote: {paths['markdown']}")
    print(f"Wrote: {paths['html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
