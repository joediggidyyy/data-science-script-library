#!/usr/bin/env python3
"""Audit environment-variable usage against optional registries (names-only).

This script scans a repository for env-var name references across code and docs,
emits names-only reports, and optionally compares observed names against one or
more JSON registry files.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclasses.dataclass(frozen=True)
class Occurrence:
    path: str
    line: int
    kind: str


@dataclasses.dataclass
class ScanResult:
    occurrences_by_var: Dict[str, List[Occurrence]]
    skipped_files: List[str]
    scanned_files: int


EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "report_tmp",
}

SKIP_DIR_PREFIXES = (
    ".venv",
)

SKIP_DIR_NAMES = {
    "site-packages",
    "dist-packages",
}

SKIP_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.example",
}

SCAN_EXTS = {
    ".py",
    ".ps1",
    ".psm1",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
}

MAX_FILE_BYTES = 2_000_000

STANDARD_ENV_VARS = {
    "ALLUSERSPROFILE",
    "APPDATA",
    "COMSPEC",
    "HOME",
    "HOMEDRIVE",
    "HOMEPATH",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PROCESSOR_IDENTIFIER",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PUBLIC",
    "PWD",
    "SHELL",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USER",
    "USERNAME",
    "USERPROFILE",
    "WINDIR",
}

RX_PY_OS_GETENV = re.compile(r"os\.getenv\(\s*['\"](?P<name>[A-Z][A-Z0-9_]{2,})['\"]")
RX_PY_ENVIRON_GET = re.compile(r"os\.environ\.get\(\s*['\"](?P<name>[A-Z][A-Z0-9_]{2,})['\"]")
RX_PY_ENVIRON_INDEX = re.compile(r"os\.environ\[\s*['\"](?P<name>[A-Z][A-Z0-9_]{2,})['\"]\s*\]")
RX_PWSH_ENV = re.compile(r"\$env:(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
RX_BRACE_REF = re.compile(r"\$\{(?P<name>[A-Z][A-Z0-9_]{2,})\}")
RX_MD_BACKTICK = re.compile(r"`(?P<name>[A-Z][A-Z0-9_]{2,})`")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_rel_posix(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def iter_candidate_files(repo_root: Path) -> Iterable[Path]:
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in SKIP_FILE_NAMES:
            continue
        if path.suffix.lower() not in SCAN_EXTS:
            continue
        parts = tuple(path.parts)
        if EXCLUDED_DIR_NAMES.intersection(set(parts)):
            continue
        if any(seg.startswith(SKIP_DIR_PREFIXES) for seg in parts):
            continue
        if SKIP_DIR_NAMES.intersection(set(parts)):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path


def extract_from_line(line: str, ext: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for rx, kind in (
        (RX_PY_OS_GETENV, "py_os_getenv"),
        (RX_PY_ENVIRON_GET, "py_environ_get"),
        (RX_PY_ENVIRON_INDEX, "py_environ_index"),
    ):
        for m in rx.finditer(line):
            out.append((kind, m.group("name")))

    for m in RX_PWSH_ENV.finditer(line):
        out.append(("pwsh_env", m.group("name").upper()))

    for m in RX_BRACE_REF.finditer(line):
        out.append(("brace_ref", m.group("name")))

    if ext == ".md" and "`" in line and "_" in line:
        for m in RX_MD_BACKTICK.finditer(line):
            out.append(("md_backtick", m.group("name")))

    return out


def scan_repo(repo_root: Path) -> ScanResult:
    occurrences_by_var: Dict[str, List[Occurrence]] = {}
    skipped_files: List[str] = []
    scanned_files = 0

    for path in iter_candidate_files(repo_root):
        rel = repo_rel_posix(repo_root, path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            skipped_files.append(rel)
            continue

        scanned_files += 1
        ext = path.suffix.lower()
        for idx, line in enumerate(text.splitlines(), start=1):
            for kind, name in extract_from_line(line, ext):
                if name in STANDARD_ENV_VARS:
                    continue
                occurrences_by_var.setdefault(name, []).append(Occurrence(path=rel, line=idx, kind=kind))

    return ScanResult(
        occurrences_by_var=occurrences_by_var,
        skipped_files=skipped_files,
        scanned_files=scanned_files,
    )


def dedupe_occurrences(occ: Sequence[Occurrence]) -> List[Occurrence]:
    seen: Set[Tuple[str, int, str]] = set()
    out: List[Occurrence] = []
    for o in occ:
        key = (o.path, o.line, o.kind)
        if key in seen:
            continue
        seen.add(key)
        out.append(o)
    return out


def prefix_summary(var_names: Iterable[str]) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for name in var_names:
        prefix = name.split("_", 1)[0] if "_" in name else name
        counts[prefix] += 1
    return dict(counts.most_common())


def _extract_names_from_registry_payload(payload: object) -> Tuple[Set[str], Set[str]]:
    names: Set[str] = set()
    aliases: Set[str] = set()

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", item):
                names.add(item)
        return names, aliases

    if not isinstance(payload, dict):
        return names, aliases

    vars_obj = payload.get("vars")
    if isinstance(vars_obj, dict):
        for key, meta in vars_obj.items():
            if isinstance(key, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", key):
                names.add(key)
            if isinstance(meta, dict):
                for alias in meta.get("aliases", []) or []:
                    if isinstance(alias, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", alias):
                        aliases.add(alias)

    env_obj = payload.get("env")
    if isinstance(env_obj, dict):
        for key in env_obj.keys():
            if isinstance(key, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", key):
                names.add(key)

    for key, value in payload.items():
        if isinstance(key, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", key):
            names.add(key)
        if isinstance(value, dict):
            for alias in value.get("aliases", []) or []:
                if isinstance(alias, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", alias):
                    aliases.add(alias)

    return names, aliases


def load_registry_names(paths: Sequence[Path]) -> Tuple[Set[str], Set[str], List[str]]:
    names: Set[str] = set()
    aliases: Set[str] = set()
    sources: List[str] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        reg_names, reg_aliases = _extract_names_from_registry_payload(payload)
        names.update(reg_names)
        aliases.update(reg_aliases)
        sources.append(str(path).replace("\\", "/"))
    return names, aliases, sources


def write_reports(
    *,
    repo_root: Path,
    out_dir: Path,
    scan: ScanResult,
    registry_names: Set[str],
    registry_aliases: Set[str],
    registry_sources: Sequence[str],
    project_prefixes: Sequence[str],
    max_occurrences_per_var: int,
    stamp: str,
) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    observed = set(scan.occurrences_by_var.keys())
    known = set(registry_names) | set(registry_aliases) | STANDARD_ENV_VARS
    unregistered_all = sorted(observed - known)

    def is_project_scoped(name: str) -> bool:
        return any(name.startswith(prefix) for prefix in project_prefixes)

    if project_prefixes:
        unregistered_project = [name for name in unregistered_all if is_project_scoped(name)]
        unregistered_other = [name for name in unregistered_all if name not in set(unregistered_project)]
    else:
        unregistered_project = list(unregistered_all)
        unregistered_other = []

    data = {
        "schema_version": "ENV_VAR_REGISTRY_AUDIT_V1",
        "generated_at_utc": _utc_now_iso(),
        "repo_root": str(repo_root).replace("\\", "/"),
        "registry_sources": list(registry_sources),
        "project_prefixes": list(project_prefixes),
        "scan": {
            "scanned_files": scan.scanned_files,
            "skipped_files_count": len(scan.skipped_files),
            "extensions": sorted(SCAN_EXTS),
        },
        "counts": {
            "registry_names": len(registry_names),
            "registry_aliases": len(registry_aliases),
            "observed_vars": len(observed),
            "unregistered_vars": len(unregistered_all),
            "unregistered_project_scoped": len(unregistered_project),
            "unregistered_other": len(unregistered_other),
        },
        "prefix_summary": prefix_summary(observed),
        "unregistered_project_scoped": [
            {
                "name": name,
                "occurrences": len(dedupe_occurrences(scan.occurrences_by_var.get(name, []))),
                "samples": [
                    dataclasses.asdict(o)
                    for o in dedupe_occurrences(scan.occurrences_by_var.get(name, []))[: max(1, int(max_occurrences_per_var))]
                ],
            }
            for name in unregistered_project
        ],
        "unregistered_other_names_sample": unregistered_other[:200],
    }

    json_path = out_dir / f"env_var_registry_audit_{stamp}.json"
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    md_lines: List[str] = []
    md_lines.append(f"# Env Var Registry Audit ({stamp})")
    md_lines.append("")
    md_lines.append("Analyze-only scan: env var names only (no values).")
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append(f"- Scanned files: {scan.scanned_files}")
    md_lines.append(f"- Observed env var names: {len(observed)}")
    md_lines.append(f"- Registry names loaded: {len(registry_names)}")
    md_lines.append(f"- Registry aliases loaded: {len(registry_aliases)}")
    md_lines.append(f"- Unregistered env var names (all): {len(unregistered_all)}")
    md_lines.append("")
    md_lines.append("## Prefix summary")
    md_lines.append("")
    for prefix, count in prefix_summary(observed).items():
        md_lines.append(f"- `{prefix}`: {count}")
    md_lines.append("")

    if unregistered_project:
        md_lines.append("## Unregistered env var names")
        md_lines.append("")
        for name in unregistered_project:
            occ = dedupe_occurrences(scan.occurrences_by_var.get(name, []))
            md_lines.append(f"### `{name}`")
            md_lines.append("")
            md_lines.append(f"Occurrences: {len(occ)}")
            md_lines.append("")
            for o in occ[: max(1, int(max_occurrences_per_var))]:
                md_lines.append(f"- `{o.path}`:{o.line} ({o.kind})")
            md_lines.append("")

    md_path = out_dir / f"env_var_registry_audit_{stamp}.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return json_path, md_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Audit env-var usage against optional registries (names-only).")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--registry-json", action="append", default=[], help="Path to a JSON registry file (repeatable)")
    ap.add_argument("--project-prefix", action="append", default=[], help="Project prefix used to classify unregistered names (repeatable)")
    ap.add_argument("--output-dir", type=Path, default=Path("report_tmp/audits/env_var_registry"))
    ap.add_argument("--max-occurrences-per-var", type=int, default=10)
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)

    repo_root = args.repo_root.resolve()
    registry_paths = [Path(p).resolve() for p in list(args.registry_json or [])]
    registry_names, registry_aliases, registry_sources = load_registry_names(registry_paths)
    scan = scan_repo(repo_root)
    stamp = args.stamp or datetime.now(timezone.utc).strftime("%Y%m%d")

    if args.dry_run:
        payload = {
            "repo_root": str(repo_root),
            "registry_sources": registry_sources,
            "observed_vars": sorted(scan.occurrences_by_var.keys()),
            "prefix_summary": prefix_summary(scan.occurrences_by_var.keys()),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    json_path, md_path = write_reports(
        repo_root=repo_root,
        out_dir=args.output_dir.resolve(),
        scan=scan,
        registry_names=registry_names,
        registry_aliases=registry_aliases,
        registry_sources=registry_sources,
        project_prefixes=list(args.project_prefix or []),
        max_occurrences_per_var=max(1, int(args.max_occurrences_per_var)),
        stamp=stamp,
    )

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())