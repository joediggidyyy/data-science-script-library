#!/usr/bin/env python3
"""trace_authority_propagation.py

## NAME

trace_authority_propagation — trace downstream candidate updates from an authority file

## SYNOPSIS

python trace_authority_propagation.py \
  --root <project-root> \
  --authority-file <path> \
  --scan-dir <path> [--scan-dir <path> ...] \
  --pattern-file <config.json> \
  --out <dir> [--output-stem <name>]

## DESCRIPTION

This script scans bounded repository surfaces for regex-defined downstream references,
legacy terms, or drift candidates that should be revisited after an authority file changes.

Pattern behavior is configured via a JSON file so the script remains environment-agnostic
and use-case agnostic. Reports are emitted as JSON and Markdown.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TEXT_SUFFIXES = [".md", ".json", ".txt", ".py", ".yaml", ".yml"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trace downstream update candidates from an authority file using a JSON pattern configuration"
    )
    parser.add_argument("--root", required=True, help="Project root to scan")
    parser.add_argument("--authority-file", required=True, help="Authority file relative to --root or absolute path")
    parser.add_argument(
        "--scan-dir",
        action="append",
        dest="scan_dirs",
        required=True,
        help="Directory relative to --root or absolute path to scan. Repeatable.",
    )
    parser.add_argument("--pattern-file", required=True, help="JSON file defining regex patterns, excerpt config, and optional surface scores")
    parser.add_argument("--out", required=True, help="Output directory for JSON/Markdown reports")
    parser.add_argument("--output-stem", default="authority_trace_candidates", help="Output filename stem without extension")
    parser.add_argument("--context-window", type=int, default=2, help="Number of context lines before and after each hit")
    parser.add_argument("--top-n", type=int, default=25, help="Number of top candidates to include in the summary report")
    parser.add_argument("--suffix", action="append", dest="suffixes", default=[], help="Additional text suffix to include, e.g. .toml. Repeatable")
    parser.add_argument("--authority-start-regex", help="Regex that marks the start of the authority excerpt block")
    parser.add_argument("--authority-end-regex", help="Regex that marks the end of the authority excerpt block")
    parser.add_argument("--include-end-line", action="store_true", help="Include the line matching --authority-end-regex in the authority excerpt")
    return parser.parse_args()


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(path_value: str | Path, root: Path) -> Path:
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def compile_flags(flag_names: list[str]) -> int:
    flags = 0
    for name in flag_names:
        try:
            flags |= getattr(re, name)
        except AttributeError as exc:
            raise ValueError(f"Unsupported regex flag: {name}") from exc
    return flags


def compile_patterns(config: dict[str, Any]) -> list[dict[str, Any]]:
    compiled = []
    for item in config.get("patterns", []):
        compiled.append(
            {
                "name": item["name"],
                "compiled": re.compile(item["regex"], compile_flags(item.get("flags", []))),
                "base_score": int(item.get("base_score", 50)),
            }
        )
    return compiled


def iter_files(paths: list[Path], suffixes: set[str]) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for base in paths:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in suffixes and path not in seen:
                seen.add(path)
                files.append(path)
    return sorted(files)


def get_context(lines: list[str], line_index: int, context_window: int) -> list[dict[str, object]]:
    start = max(0, line_index - context_window)
    end = min(len(lines), line_index + context_window + 1)
    return [{"line": idx + 1, "text": lines[idx]} for idx in range(start, end)]


def classify_surface(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    return rel.split("/", 1)[0]


def score_hit(surface: str, base_score: int, surface_scores: dict[str, int]) -> int:
    return base_score + int(surface_scores.get(surface, 0))


def extract_authority_excerpt(text: str, excerpt_config: dict[str, Any]) -> list[str]:
    start_regex = excerpt_config.get("start_regex")
    end_regex = excerpt_config.get("end_regex")
    include_end = bool(excerpt_config.get("include_end", False))
    if not start_regex:
        return []

    start_pattern = re.compile(start_regex)
    end_pattern = re.compile(end_regex) if end_regex else None
    lines = text.splitlines()
    capture = False
    excerpt: list[str] = []

    for line in lines:
        if not capture and start_pattern.search(line):
            capture = True
        if capture:
            if end_pattern and end_pattern.search(line):
                if include_end:
                    excerpt.append(line)
                break
            excerpt.append(line)
    return excerpt


def build_summary(
    *,
    authority_file: Path,
    authority_excerpt: list[str],
    scan_dirs: list[Path],
    root: Path,
    results: list[dict[str, Any]],
    top_n: int,
) -> dict[str, Any]:
    hits_by_surface: dict[str, int] = defaultdict(int)
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        hits_by_surface[item["surface"]] += 1
        by_file[item["path"]].append(item)

    return {
        "generated_at_utc": utc_now_iso(),
        "authority_file": authority_file.relative_to(root).as_posix(),
        "authority_excerpt": authority_excerpt,
        "scan_roots": [path.relative_to(root).as_posix() for path in scan_dirs if path.exists()],
        "total_hits": len(results),
        "files_with_hits": len(by_file),
        "hits_by_surface": dict(sorted(hits_by_surface.items())),
        "top_candidates": results[:top_n],
        "all_results": results,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in summary["all_results"]:
        by_file[item["path"]].append(item)

    lines: list[str] = []
    lines.append("# Authority Trace Candidate Report")
    lines.append("")
    lines.append("## Authority source")
    lines.append("")
    lines.append(f"- Authoritative source: `{summary['authority_file']}`")
    lines.append(f"- Generated at (UTC): `{summary['generated_at_utc']}`")
    lines.append("- Bounded scan roots: {}".format(", ".join(f"`{item}`" for item in summary["scan_roots"])))
    lines.append(f"- Files with hits: {summary['files_with_hits']}")
    lines.append(f"- Total hits: {summary['total_hits']}")
    lines.append("")

    if summary["authority_excerpt"]:
        lines.append("### Extracted authority excerpt")
        lines.append("")
        lines.append("```text")
        lines.extend(summary["authority_excerpt"])
        lines.append("```")
        lines.append("")

    lines.append("## Hits by surface")
    lines.append("")
    for surface, count in summary["hits_by_surface"].items():
        lines.append(f"- `{surface}`: {count}")
    lines.append("")
    lines.append("## Ranked update candidates")
    lines.append("")

    for path_key in sorted(by_file):
        hits = sorted(by_file[path_key], key=lambda item: (-item["score"], item["line"]))
        lines.append(f"### `{path_key}`")
        lines.append("")
        lines.append(f"- surface: `{hits[0]['surface']}`")
        lines.append(f"- max score: `{hits[0]['score']}`")
        lines.append("- hit kinds: {}".format(", ".join(sorted({item["kind"] for item in hits}))))
        lines.append("")
        for item in hits[:6]:
            lines.append(f"- line {item['line']} [{item['kind']}]: `{item['match_text'].strip()}`")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    pattern_config = load_json_file(Path(args.pattern_file).resolve())
    excerpt_config = dict(pattern_config.get("authority_excerpt", {}))
    if args.authority_start_regex:
        excerpt_config["start_regex"] = args.authority_start_regex
    if args.authority_end_regex:
        excerpt_config["end_regex"] = args.authority_end_regex
    if args.include_end_line:
        excerpt_config["include_end"] = True

    authority_file = resolve_path(args.authority_file, root)
    scan_dirs = [resolve_path(item, root) for item in args.scan_dirs]
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    suffixes = {suffix.lower() for suffix in DEFAULT_TEXT_SUFFIXES}
    suffixes.update(suffix.lower() for suffix in pattern_config.get("text_suffixes", []))
    suffixes.update(suffix.lower() for suffix in args.suffixes)

    compiled_patterns = compile_patterns(pattern_config)
    surface_scores = pattern_config.get("surface_scores", {})

    authority_text = authority_file.read_text(encoding="utf-8")
    authority_excerpt = extract_authority_excerpt(authority_text, excerpt_config)

    results: list[dict[str, Any]] = []
    for path in iter_files(scan_dirs, suffixes):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        rel = path.relative_to(root)
        surface = classify_surface(path, root)

        for pattern in compiled_patterns:
            for match in pattern["compiled"].finditer(text):
                line_index = text[: match.start()].count("\n")
                results.append(
                    {
                        "path": rel.as_posix(),
                        "surface": surface,
                        "kind": pattern["name"],
                        "line": line_index + 1,
                        "match_text": match.group(0),
                        "base_score": pattern["base_score"],
                        "score": score_hit(surface, pattern["base_score"], surface_scores),
                        "context": get_context(lines, line_index, args.context_window),
                    }
                )

    results.sort(key=lambda item: (-item["score"], item["path"], item["line"]))
    summary = build_summary(
        authority_file=authority_file,
        authority_excerpt=authority_excerpt,
        scan_dirs=scan_dirs,
        root=root,
        results=results,
        top_n=args.top_n,
    )

    json_report = out_dir / f"{args.output_stem}.json"
    md_report = out_dir / f"{args.output_stem}.md"
    json_report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_report.write_text(render_markdown(summary), encoding="utf-8")

    print(f"Wrote: {json_report}")
    print(f"Wrote: {md_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())