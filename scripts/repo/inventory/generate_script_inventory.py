#!/usr/bin/env python3
"""generate_script_inventory.py

## NAME

generate_script_inventory — scan a directory for scripts and emit an inventory report

## SYNOPSIS

python generate_script_inventory.py --root <path> --out <dir> [--use-git]

## DESCRIPTION

Builds a simple inventory of script-like files under a root directory.

- Detects common script extensions (`.py`, `.ps1`, `.sh`, `.bat`, etc.)
- Records basic filesystem metadata
- Optionally enriches each file with its last git commit timestamp (if `git` is available)

Outputs:
- JSON inventory
- Markdown inventory (human-readable)

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


SCRIPT_EXTS = {".py", ".ps1", ".sh", ".bat", ".psm1", ".psd1"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_stat(path: Path) -> dict:
    st = path.stat()
    return {
        "size_bytes": st.st_size,
        "last_modified_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
    }


def iter_scripts(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in SCRIPT_EXTS:
            yield p


def git_last_commit_iso(repo_root: Path, file_path: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "--", str(file_path)],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
        )
        s = out.decode("utf-8", errors="ignore").strip()
        return s or None
    except Exception:
        return None


def describe_file(path: Path) -> str:
    """Extract a short description from the first docstring/comment line."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

    lines = [l.strip() for l in text.splitlines()][:60]

    # docstring
    for i, l in enumerate(lines):
        if l.startswith('"""') or l.startswith("'''"):
            # single-line docstring
            if l.count('"""') >= 2 or l.count("'''") >= 2:
                return l.strip('"\'')[:200]
            # multi-line: collect until terminator
            quote = '"""' if l.startswith('"""') else "'''"
            desc = l.lstrip('"\'')
            j = i + 1
            while j < len(lines) and quote not in lines[j]:
                if lines[j]:
                    desc += " " + lines[j]
                j += 1
            return desc.strip()[:200]

    # first comment line
    for l in lines:
        if l.startswith("#"):
            return l.lstrip("# ").strip()[:200]

    # fallback: first non-empty
    for l in lines:
        if l:
            return l[:200]

    return ""


def write_markdown(entries: list[dict], out_path: Path) -> None:
    lines: list[str] = []
    lines.append("# Script Inventory")
    lines.append("")
    lines.append(f"> Generated at (UTC): `{utc_now_iso()}`")
    lines.append("")
    lines.append(f"Total scripts: **{len(entries)}**")
    lines.append("")

    for e in entries:
        lines.append(f"- `{e['path']}`")
        if e.get("description"):
            lines.append(f"  - {e['description']}")
        lines.append(f"  - size_bytes: {e.get('size_bytes')}")
        lines.append(f"  - last_modified_utc: {e.get('last_modified_utc')}")
        if e.get("last_commit_iso"):
            lines.append(f"  - last_commit_iso: {e.get('last_commit_iso')}")

    lines.append("")
    lines.append("---")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a repository scripts inventory (JSON + Markdown)")
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--use-git", action="store_true", help="Attempt to enrich with git last-commit timestamps")

    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve()

    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []

    for p in sorted(iter_scripts(root)):
        rel = str(p.relative_to(root)).replace("\\", "/")
        meta = safe_stat(p)
        entry = {
            "path": rel,
            "abs_path": str(p),
            **meta,
            "description": describe_file(p),
        }
        if args.use_git:
            entry["last_commit_iso"] = git_last_commit_iso(root, p)
        entries.append(entry)

    payload = {
        "generated_at_utc": utc_now_iso(),
        "root": str(root),
        "total": len(entries),
        "entries": entries,
    }

    json_out = out_dir / "script_inventory.json"
    md_out = out_dir / "script_inventory.md"

    json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(entries, md_out)

    print(f"Wrote: {json_out}")
    print(f"Wrote: {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
