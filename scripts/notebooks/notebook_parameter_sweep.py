"""notebook_parameter_sweep.py

Run a Jupyter notebook over a parameter grid.

This is a lightweight alternative to tools like papermill. It works by:
1) inserting (or replacing) a code cell tagged "parameters"
2) optionally executing the notebook via nbconvert's ExecutePreprocessor
3) writing one output notebook per parameter set + a JSON summary

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


@dataclass
class SweepRunResult:
    index: int
    parameters: Dict[str, Any]
    output_notebook: str
    ok: bool
    error: Optional[str]
    elapsed_sec: float


def _parse_kv_params(items: Sequence[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --params entry (expected k=v): {item!r}")
        k, v = item.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            raise ValueError(f"Invalid --params entry (empty key): {item!r}")
        try:
            params[k] = json.loads(v)
        except Exception:
            params[k] = v
    return params


def _python_literal(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return repr(value)
    # fall back to JSON if possible, otherwise repr
    try:
        return json.dumps(value)
    except Exception:
        return repr(value)


def render_parameters_cell(parameters: Dict[str, Any]) -> str:
    lines = [
        "# Parameters injected by notebook_parameter_sweep.py",
    ]
    for key in sorted(parameters.keys()):
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise ValueError(
                f"Parameter name is not a valid Python identifier: {key!r}"
            )
        lines.append(f"{key} = {_python_literal(parameters[key])}")
    lines.append("")
    return "\n".join(lines)


def apply_parameters_to_notebook(nb: Any, parameters: Dict[str, Any]) -> Any:
    """Insert or replace a 'parameters' tagged cell."""

    cell_source = render_parameters_cell(parameters)

    # Find existing cell with tag "parameters"
    for cell in nb.get("cells", []):
        tags = []
        md = cell.get("metadata")
        if isinstance(md, dict):
            tags = md.get("tags") or []
        if isinstance(tags, list) and "parameters" in tags and cell.get("cell_type") == "code":
            cell["source"] = cell_source
            return nb

    # Otherwise, insert a new code cell at the top
    new_cell = nbformat.v4.new_code_cell(cell_source)
    new_cell.metadata["tags"] = ["parameters"]
    nb.cells.insert(0, new_cell)
    return nb


def execute_notebook(
    nb: Any,
    *,
    kernel_name: str,
    timeout_sec: int,
    cwd: Path,
    allow_errors: bool,
) -> Any:
    ep = ExecutePreprocessor(
        timeout=timeout_sec,
        kernel_name=kernel_name,
        allow_errors=allow_errors,
    )
    ep.preprocess(nb, {"metadata": {"path": str(cwd)}})
    return nb


def sweep_notebook(
    input_path: Path,
    outdir: Path,
    runs: Sequence[Dict[str, Any]],
    *,
    execute: bool,
    kernel_name: str,
    timeout_sec: int,
    cwd: Path,
    allow_errors: bool,
) -> List[SweepRunResult]:
    input_path = input_path.resolve()
    outdir = outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        base_nb = nbformat.read(f, as_version=4)

    results: List[SweepRunResult] = []

    for i, params in enumerate(runs):
        start = time.time()
        nb = copy.deepcopy(base_nb)
        apply_parameters_to_notebook(nb, params)

        ok = True
        err: Optional[str] = None
        if execute:
            try:
                execute_notebook(
                    nb,
                    kernel_name=kernel_name,
                    timeout_sec=timeout_sec,
                    cwd=cwd,
                    allow_errors=allow_errors,
                )
            except Exception as e:
                ok = False
                err = f"{type(e).__name__}: {e}"
                if not allow_errors:
                    raise

        out_path = outdir / f"{input_path.stem}__run{i:03d}.ipynb"
        with out_path.open("w", encoding="utf-8") as wf:
            nbformat.write(nb, wf)

        elapsed = time.time() - start
        results.append(
            SweepRunResult(
                index=i,
                parameters=dict(params),
                output_notebook=str(out_path),
                ok=ok,
                error=err,
                elapsed_sec=elapsed,
            )
        )

    return results


def _load_grid(grid_path: Path) -> List[Dict[str, Any]]:
    raw = json.loads(grid_path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list) and all(isinstance(x, dict) for x in raw):
        return raw  # type: ignore[return-value]
    raise ValueError("Grid JSON must be a dict or a list of dicts")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a notebook over a parameter grid")
    parser.add_argument("notebook", help="Path to .ipynb file")
    parser.add_argument(
        "--outdir",
        default=None,
        help="Output directory (default: <notebook>_sweep next to input)",
    )
    parser.add_argument(
        "--grid",
        default=None,
        help="JSON file containing a dict or list[dict] of parameters",
    )
    parser.add_argument(
        "--params",
        action="append",
        default=[],
        help="Single-run parameters as k=v (value parsed as JSON when possible). Can repeat.",
    )
    parser.add_argument(
        "--no-execute",
        action="store_true",
        help="Only write parameterized notebooks; do not execute",
    )
    parser.add_argument("--kernel", default="python3", help="Jupyter kernel name")
    parser.add_argument("--timeout-sec", type=int, default=300, help="Cell timeout")
    parser.add_argument(
        "--cwd",
        default=None,
        help="Working directory for execution (default: input notebook's folder)",
    )
    parser.add_argument(
        "--allow-errors",
        action="store_true",
        help="Continue even if execution errors occur (errors recorded in report)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Write JSON summary (default: <outdir>/sweep_report.json)",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = Path(args.notebook)
    if not input_path.exists():
        print(f"Error: notebook not found: {input_path}", file=sys.stderr)
        return 2

    outdir = Path(args.outdir) if args.outdir else input_path.with_name(input_path.stem + "_sweep")
    cwd = Path(args.cwd) if args.cwd else input_path.parent

    runs: List[Dict[str, Any]] = []
    if args.grid:
        runs.extend(_load_grid(Path(args.grid)))
    if args.params:
        runs.append(_parse_kv_params(args.params))

    if not runs:
        print("Error: provide --grid or at least one --params k=v", file=sys.stderr)
        return 2

    results = sweep_notebook(
        input_path,
        outdir,
        runs,
        execute=not bool(args.no_execute),
        kernel_name=str(args.kernel),
        timeout_sec=int(args.timeout_sec),
        cwd=cwd,
        allow_errors=bool(args.allow_errors),
    )

    report_path = Path(args.report) if args.report else (outdir / "sweep_report.json")
    report_path.write_text(
        json.dumps([r.__dict__ for r in results], indent=2), encoding="utf-8"
    )

    ok_count = sum(1 for r in results if r.ok)
    print(f"Runs: {len(results)} (ok: {ok_count}, failed: {len(results) - ok_count})")
    print(f"Outdir: {outdir}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
