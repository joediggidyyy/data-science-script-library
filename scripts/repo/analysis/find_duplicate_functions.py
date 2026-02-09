#!/usr/bin/env python3
"""find_duplicate_functions.py

## NAME

find_duplicate_functions — detect exact duplicate function bodies across Python files

## SYNOPSIS

python find_duplicate_functions.py --root <dir> --out <dir>

## DESCRIPTION

This script parses Python files under a root directory, extracts top-level
function definitions, and hashes a normalized AST dump of each function body.

It reports groups of identical hashes found in 2+ locations.

Outputs:
- JSON report
- Markdown report

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iter_py_files(root: Path) -> Iterable[Path]:
    if root.is_file() and root.suffix.lower() == ".py":
        yield root
        return
    for p in root.rglob("*.py"):
        if not p.is_file():
            continue
        # skip common bulky dirs
        parts = {x.lower() for x in p.parts}
        if any(x in parts for x in (".git", "__pycache__", ".venv", "venv", "site-packages")):
            continue
        yield p


def normalized_ast_dump(node: ast.AST) -> str:
    # Remove attributes like lineno/col_offset to produce stable dumps
    for n in ast.walk(node):
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if hasattr(n, attr):
                try:
                    setattr(n, attr, None)
                except Exception:
                    pass
    return ast.dump(node, include_attributes=False)


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_functions(path: Path) -> list[dict]:
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return []

    try:
        mod = ast.parse(src)
    except SyntaxError:
        return []

    funcs: list[dict] = []
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            dump = normalized_ast_dump(node)
            funcs.append(
                {
                    "name": node.name,
                    "lineno": getattr(node, "lineno", None),
                    "hash": hash_text(dump),
                }
            )
    return funcs


def write_markdown(dupes: list[dict], out_path: Path) -> None:
    lines: list[str] = []
    lines.append("# Duplicate functions report")
    lines.append("")
    lines.append(f"> Generated at (UTC): `{utc_now_iso()}`")
    lines.append("")
    lines.append(f"Duplicate groups: **{len(dupes)}**")
    lines.append("")

    for g in dupes:
        lines.append(f"## {g['function_hash']}")
        lines.append("")
        for occ in g["occurrences"]:
            lines.append(f"- `{occ['path']}`:{occ.get('lineno') or '-'} — `{occ['name']}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find exact duplicate Python functions across a directory")
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--out", required=True, help="Output directory")

    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve()

    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    out_dir.mkdir(parents=True, exist_ok=True)

    func_index: dict[str, list[dict]] = defaultdict(list)

    for fp in sorted(iter_py_files(root)):
        rel = str(fp.relative_to(root)).replace("\\", "/")
        for f in extract_functions(fp):
            func_index[f["hash"]].append({"path": rel, "name": f["name"], "lineno": f.get("lineno")})

    dupes: list[dict] = []
    for h, occurrences in func_index.items():
        if len(occurrences) > 1:
            dupes.append({"function_hash": h, "occurrences": occurrences})

    dupes.sort(key=lambda d: len(d["occurrences"]), reverse=True)

    payload = {
        "generated_at_utc": utc_now_iso(),
        "root": str(root),
        "duplicate_groups": len(dupes),
        "groups": dupes,
    }

    json_out = out_dir / "duplicate_functions_report.json"
    md_out = out_dir / "duplicate_functions_report.md"

    json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(dupes, md_out)

    print(f"Wrote: {json_out}")
    print(f"Wrote: {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
