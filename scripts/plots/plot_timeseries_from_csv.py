#!/usr/bin/env python3
"""plot_timeseries_from_csv.py

## NAME

plot_timeseries_from_csv — quick time-series line charts from a CSV file

## SYNOPSIS

python plot_timeseries_from_csv.py <in_csv> --out plot.png [--x timestamp] [--y value]

## DESCRIPTION

This script creates a simple line chart from CSV data with sensible defaults.
It is intended for quick plotting during analytics/DS coursework:

- reads a CSV with a header row
- uses `--x` as the x-axis column (defaults to the first column)
- uses one or more `--y` columns as series (defaults to numeric-looking columns)
- writes a PNG plot via matplotlib (headless-safe)

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _try_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except Exception:
        return None


_DT_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
]


def _try_datetime(s: str) -> Optional[datetime]:
    ss = s.strip()
    if not ss:
        return None

    # ISO-ish (including trailing Z)
    try:
        iso = ss.replace("Z", "+00:00")
        return datetime.fromisoformat(iso)
    except Exception:
        pass

    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(ss, fmt)
        except Exception:
            continue

    return None


def _detect_numeric_columns(rows: list[dict[str, str]], *, exclude: set[str], sample: int = 50) -> list[str]:
    if not rows:
        return []

    keys = [k for k in rows[0].keys() if k not in exclude]
    numeric: list[str] = []

    for k in keys:
        ok = 0
        seen = 0
        for r in rows[:sample]:
            v = (r.get(k) or "").strip()
            if v == "":
                continue
            seen += 1
            if _try_float(v) is not None:
                ok += 1

        # Heuristic: if we saw any values and most were numeric, treat as numeric.
        if seen > 0 and ok / seen >= 0.8:
            numeric.append(k)

    return numeric


def plot_timeseries_from_csv(
    in_csv: Path,
    out_path: Path,
    *,
    x_col: str,
    y_cols: list[str],
    encoding: str = "utf-8",
    delimiter: str = ",",
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
) -> None:
    with in_csv.open("r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV appears to have no header row")
        header = list(reader.fieldnames)

        if x_col not in header:
            raise ValueError(f"x column '{x_col}' not found in CSV header")

        for y in y_cols:
            if y not in header:
                raise ValueError(f"y column '{y}' not found in CSV header")

        rows = [row for row in reader]

    # Parse x values: datetime if possible else float if possible else row index.
    x_raw = [(r.get(x_col) or "").strip() for r in rows]

    x_dt = [_try_datetime(v) for v in x_raw]
    is_dt = all(v is not None for v in x_dt if v != "") and any(v is not None for v in x_dt)

    if is_dt:
        x_vals: list[Any] = [v if v is not None else None for v in x_dt]
        x_kind = "datetime"
    else:
        x_num = [_try_float(v) for v in x_raw]
        if any(v is not None for v in x_num):
            x_vals = [v if v is not None else None for v in x_num]
            x_kind = "number"
        else:
            x_vals = list(range(len(rows)))
            x_kind = "index"

    # Parse y series.
    series: dict[str, list[Optional[float]]] = {k: [] for k in y_cols}
    for r in rows:
        for k in y_cols:
            s = (r.get(k) or "").strip()
            series[k].append(_try_float(s) if s != "" else None)

    # Import matplotlib only when needed; use Agg backend for headless environments.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 5))

    for name, ys in series.items():
        xs_plot: list[Any] = []
        ys_plot: list[float] = []
        for x, y in zip(x_vals, ys):
            if y is None or x is None:
                continue
            xs_plot.append(x)
            ys_plot.append(y)
        if xs_plot:
            plt.plot(xs_plot, ys_plot, label=name)

    if title:
        plt.title(title)

    plt.xlabel(xlabel or x_col)
    plt.ylabel(ylabel or (y_cols[0] if len(y_cols) == 1 else "value"))

    if len(y_cols) > 1:
        plt.legend()

    if x_kind == "datetime":
        plt.gcf().autofmt_xdate()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Plot a timeseries line chart from a CSV file")
    parser.add_argument("in_csv", help="Input CSV file")
    parser.add_argument("--out", required=True, help="Output image path (PNG)")
    parser.add_argument("--x", dest="x_col", default=None, help="X-axis column (default: first column)")
    parser.add_argument(
        "--y",
        dest="y_cols",
        action="append",
        default=None,
        help="Y-axis column to plot (repeatable). If omitted, numeric-looking columns are plotted.",
    )
    parser.add_argument("--encoding", default="utf-8", help="Text encoding")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter")
    parser.add_argument("--title", default="", help="Plot title")
    parser.add_argument("--xlabel", default="", help="X label")
    parser.add_argument("--ylabel", default="", help="Y label")

    args = parser.parse_args(argv)

    in_path = Path(args.in_csv).resolve()
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    out_path = Path(args.out).resolve()

    # Peek header + rows for y-col inference.
    with in_path.open("r", encoding=args.encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=args.delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV appears to have no header row")
        header = list(reader.fieldnames)
        rows = [row for row in reader]

    x_col = args.x_col or header[0]

    if args.y_cols:
        y_cols = list(args.y_cols)
    else:
        y_cols = _detect_numeric_columns(rows, exclude={x_col})

    if not y_cols:
        raise ValueError("Could not infer any numeric y columns; pass one or more --y <col>")

    plot_timeseries_from_csv(
        in_path,
        out_path,
        x_col=x_col,
        y_cols=y_cols,
        encoding=args.encoding,
        delimiter=args.delimiter,
        title=args.title,
        xlabel=args.xlabel,
        ylabel=args.ylabel,
    )

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
