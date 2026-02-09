#!/usr/bin/env python3
"""find_near_duplicate_functions.py

## NAME

find_near_duplicate_functions — detect near-duplicate Python functions (AST-normalized fuzzy matching)

## SYNOPSIS

python find_near_duplicate_functions.py --root <dir> --out <dir> [--threshold 0.75]

## DESCRIPTION

Parses Python files under a root directory, extracts top-level functions, and
compares normalized AST dumps using difflib similarity.

This is intended to highlight refactoring candidates (same logic with small edits).

Outputs:
- JSON report
- Markdown report

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
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
        parts = {x.lower() for x in p.parts}
        if any(x in parts for x in (".git", "__pycache__", ".venv", "venv", "site-packages")):
            continue
        yield p


def normalized_function_body_dump(node: ast.AST) -> str | None:
    """Name-agnostic normalized AST dump for a function node."""
    import copy

    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None

    try:
        n = copy.deepcopy(node)
    except Exception:
        return None

    # normalize function name
    n.name = "FUNC"

    # normalize argument names
    arg_map: dict[str, str] = {}
    try:
        for i, a in enumerate(getattr(n.args, "args", [])):
            if isinstance(a, ast.arg):
                arg_map[a.arg] = f"ARG{i}"
                a.arg = f"ARG{i}"
        if getattr(n.args, "vararg", None) is not None:
            arg_map[n.args.vararg.arg] = "VARARG"
            n.args.vararg.arg = "VARARG"
        if getattr(n.args, "kwarg", None) is not None:
            arg_map[n.args.kwarg.arg] = "KWARG"
            n.args.kwarg.arg = "KWARG"
    except Exception:
        pass

    name_map: dict[str, str] = {}
    counter = 0

    for t in ast.walk(n):
        if isinstance(t, ast.Name):
            ident = t.id
            if ident in ("True", "False", "None"):
                continue
            if ident in arg_map:
                t.id = arg_map[ident]
                continue
            if ident not in name_map:
                name_map[ident] = f"VAR{counter}"
                counter += 1
            t.id = name_map[ident]

        if isinstance(t, ast.arg):
            if t.arg in arg_map:
                t.arg = arg_map[t.arg]

    # strip line numbers
    for t in ast.walk(n):
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if hasattr(t, attr):
                try:
                    setattr(t, attr, None)
                except Exception:
                    pass

    try:
        return ast.dump(n, include_attributes=False)
    except Exception:
        return None


def collect_functions(root: Path) -> list[dict]:
    out: list[dict] = []
    for fp in sorted(iter_py_files(root)):
        rel = str(fp.relative_to(root)).replace("\\", "/")
        try:
            src = fp.read_text(encoding="utf-8")
            mod = ast.parse(src)
        except Exception:
            continue

        for node in mod.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nd = normalized_function_body_dump(node)
                if not nd:
                    continue
                out.append({"path": rel, "name": node.name, "lineno": getattr(node, "lineno", None), "normalized_dump": nd})

    return out


def bucket_key(s: str) -> int:
    return len(s) // 120


def write_markdown(pairs: list[dict], threshold: float, out_path: Path) -> None:
    lines: list[str] = []
    lines.append("# Near-duplicate functions report")
    lines.append("")
    lines.append(f"> Generated at (UTC): `{utc_now_iso()}`")
    lines.append("")
    lines.append(f"> Similarity threshold: **{threshold}**")
    lines.append("")
    lines.append(f"Pairs found: **{len(pairs)}**")
    lines.append("")

    for p in pairs[:200]:
        a = p["a"]; b = p["b"]; r = p["ratio"]
        lines.append(f"- {r:.2f}: `{a['path']}`:{a.get('lineno') or '-'} `{a['name']}`  <=>  `{b['path']}`:{b.get('lineno') or '-'} `{b['name']}`")

    lines.append("")
    lines.append("---")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find near-duplicate Python functions (AST-normalized fuzzy matching)")
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--threshold", type=float, default=0.75, help="Similarity threshold")

    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve()

    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    out_dir.mkdir(parents=True, exist_ok=True)

    funcs = collect_functions(root)

    # bucket by dump length
    buckets: dict[int, list[dict]] = defaultdict(list)
    for f in funcs:
        buckets[bucket_key(f["normalized_dump"])].append(f)

    pairs: list[dict] = []
    keys = sorted(buckets.keys())
    for k in keys:
        candidates = buckets[k] + buckets.get(k - 1, []) + buckets.get(k + 1, [])
        L = len(candidates)
        for i in range(L):
            a = candidates[i]
            for j in range(i + 1, L):
                b = candidates[j]
                if a["path"] == b["path"] and a.get("lineno") == b.get("lineno"):
                    continue

                la = len(a["normalized_dump"])
                lb = len(b["normalized_dump"])
                if abs(la - lb) > max(120, min(la, lb) * 0.35):
                    continue

                r = SequenceMatcher(None, a["normalized_dump"], b["normalized_dump"]).ratio()
                if r >= args.threshold:
                    pairs.append({"a": a, "b": b, "ratio": r})

    pairs.sort(key=lambda x: x["ratio"], reverse=True)

    payload = {
        "generated_at_utc": utc_now_iso(),
        "root": str(root),
        "threshold": args.threshold,
        "pairs_found": len(pairs),
        "pairs": pairs[:500],
    }

    json_out = out_dir / "near_duplicate_functions_report.json"
    md_out = out_dir / "near_duplicate_functions_report.md"

    json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(pairs, args.threshold, md_out)

    print(f"Wrote: {json_out}")
    print(f"Wrote: {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
