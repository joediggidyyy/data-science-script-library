#!/usr/bin/env python3
"""check_command_blocks.py

## NAME

check_command_blocks — flag command-like lines outside fenced code blocks

## SYNOPSIS

python check_command_blocks.py <path-or-directory> [--ext .md] [--max-samples 40]

## DESCRIPTION

This script scans Markdown files and flags shell-style command lines that appear
outside fenced code blocks. It helps keep READMEs and reports copy/paste safe
and avoids accidental execution instructions being mixed into prose.

Exit code:
- 0: no violations
- 1: violations found

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


CMD_PREFIXES_DEFAULT = [
    "python",
    "pip",
    "git",
    "docker",
    "curl",
    "npm",
    "yarn",
    "pytest",
    "pwsh",
    "powershell",
]


def iter_markdown_files(root: Path, ext: str) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for p in root.rglob(f"*{ext}"):
        if p.is_file():
            yield p


def scan_file(path: Path, cmd_re: re.Pattern[str]) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    violations: list[tuple[int, str]] = []

    in_fence = False
    fence_backtick_count = 0

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        m_fence = re.match(r"^(\s*)(`{3,})(.*)$", line)
        if m_fence:
            ticks = m_fence.group(2)
            if not in_fence:
                in_fence = True
                fence_backtick_count = len(ticks)
            else:
                if len(ticks) >= fence_backtick_count:
                    in_fence = False
                    fence_backtick_count = 0
            continue

        if in_fence:
            continue

        # Skip headings; they can legitimately start with words like "Python"
        if line.strip().startswith("#"):
            continue

        m_cmd = cmd_re.match(line)
        if m_cmd:
            matched_prefix = m_cmd.group(1)
            # Avoid false positives where the word is used as prose/title-case.
            if matched_prefix != matched_prefix.lower():
                continue
            violations.append((i, line))

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan markdown files and flag plaintext command lines outside code fences")
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("--ext", default=".md", help="File extension to scan (default: .md)")
    parser.add_argument("--max-samples", type=int, default=40, help="Max files to show in report")
    parser.add_argument("--prefix", action="append", default=None, help="Command prefix to flag (repeatable)")

    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        sys.stderr.write(f"[FAIL] Path not found: {root}\n")
        return 2

    prefixes = args.prefix if args.prefix else CMD_PREFIXES_DEFAULT
    cmd_re = re.compile(r"^\s*(" + "|".join(re.escape(p) for p in prefixes) + r")\b", re.IGNORECASE)

    offenders: list[tuple[Path, list[tuple[int, str]]]] = []
    total = 0

    for md in sorted(iter_markdown_files(root, args.ext)):
        v = scan_file(md, cmd_re)
        if v:
            offenders.append((md, v))
            total += len(v)

    if not offenders:
        print("OK — no plaintext command violations found.")
        return 0

    print(f"Found {total} plaintext command lines outside code blocks.")
    print("Sample locations:")
    for md, violations in offenders[: args.max_samples]:
        print(f" - {md} ({len(violations)}):")
        for ln, text in violations[:5]:
            print(f"    {ln}: {text.strip()}")

    print("\nWrap command lines in fenced code blocks to resolve.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
