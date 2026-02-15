#!/usr/bin/env python3
"""clean_unicode.py

## NAME

clean_unicode — replace common unicode punctuation/symbols with ASCII-safe equivalents

## SYNOPSIS

python clean_unicode.py <path-or-directory> [--ext .md] [--inplace] [--backup-suffix .bak]

## DESCRIPTION

This script scans text files and replaces a small set of common unicode characters
(e.g., smart quotes, arrows, ellipsis) with ASCII equivalents.

By default, it prints a summary and does not modify files unless `--inplace` is provided.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable


REPLACEMENTS = {
    "\ufeff": "",      # BOM
    "\u2192": "->",    # →
    "\u2190": "<-",    # ←
    "\u2022": "*",     # •
    "\u2013": "-",     # –
    "\u2014": "--",    # —
    "\u2018": "'",     # ‘
    "\u2019": "'",     # ’
    "\u201c": '"',     # “
    "\u201d": '"',     # ”
    "\u2026": "...",   # …
    "\u2713": "[OK]",  # ✓
    "\u2717": "[FAIL]",# ✗
    "\u2794": "->",    # ➔
}


def iter_files(root: Path, ext: str) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for p in root.rglob(f"*{ext}"):
        if p.is_file():
            yield p


def transform_text(text: str) -> tuple[str, int]:
    changed = 0
    out = text
    for u, a in REPLACEMENTS.items():
        if u in out:
            out = out.replace(u, a)
            changed += 1
    return out, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace common unicode punctuation with ASCII equivalents")
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("--ext", default=".md", help="File extension filter when scanning directories")
    parser.add_argument("--inplace", action="store_true", help="Modify files in place")
    parser.add_argument("--backup-suffix", default=".bak", help="Backup suffix when writing in place")

    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"[FAIL] Path not found: {root}")
        return 2

    touched = 0
    modified = 0

    for fp in sorted(iter_files(root, args.ext)):
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[WARN] Could not read: {fp} ({e})")
            continue

        new_text, change_count = transform_text(text)
        touched += 1

        if new_text != text:
            if args.inplace:
                backup = fp.with_suffix(fp.suffix + args.backup_suffix)
                try:
                    backup.write_text(text, encoding="utf-8")
                    fp.write_text(new_text, encoding="utf-8")
                    print(f"[OK] Cleaned {fp} (backup: {backup.name})")
                except Exception as e:
                    print(f"[FAIL] Could not write: {fp} ({e})")
                    continue
            else:
                print(f"[INFO] Would clean {fp}")
            modified += 1

    print(f"\nScanned: {touched} | Changed: {modified} | Inplace: {args.inplace}")
    return 0 if modified == 0 or args.inplace else 1


if __name__ == "__main__":
    raise SystemExit(main())
