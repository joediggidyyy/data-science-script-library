"""VS Code crash/instability audit collector.

Purpose
- Collect deterministic crash-triage evidence from local VS Code logs.
- Emit machine-readable + human-readable artifacts.

Modes
- --dry-run : analyze and print summary only
- --apply   : write JSON/Markdown artifacts
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REDACT_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[A-Za-z0-9\-\._~\+/]+=*"), r"\1<REDACTED_BEARER>"),
    (re.compile(r"\b[A-Za-z0-9\-_]{48,}\b"), "<REDACTED_LONG_TOKEN>"),
)

SIGNAL_PATTERNS: Dict[str, re.Pattern[str]] = {
    "listener_leak": re.compile(r"listener\s+LEAK", re.IGNORECASE),
    "extension_unresponsive": re.compile(r"extension host.*unresponsive", re.IGNORECASE),
    "uri_error": re.compile(r"UriError", re.IGNORECASE),
    "polling_failed": re.compile(r"Polling failed", re.IGNORECASE),
    "channel_closed": re.compile(r"Channel has been closed", re.IGNORECASE),
    "dispose_error": re.compile(r"dispose|disposing", re.IGNORECASE),
    "crash_or_fatal": re.compile(r"crash|fatal|out of memory|oom", re.IGNORECASE),
}


@dataclass
class AuditPaths:
    repo_root: Path
    out_dir: Path
    json_path: Path
    md_path: Path


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _redact(text: str) -> str:
    out = text
    for pattern, repl in REDACT_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def _read_tail(path: Path, max_lines: int) -> List[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    return [_redact(line) for line in lines[-max_lines:]]


def _score_signals(lines: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {name: 0 for name in SIGNAL_PATTERNS}
    for line in lines:
        for name, pattern in SIGNAL_PATTERNS.items():
            if pattern.search(line):
                counts[name] += 1
    return counts


def _extract_signal_lines(lines: List[str], max_hits: int = 60) -> List[Dict[str, object]]:
    hits: List[Dict[str, object]] = []
    for idx, line in enumerate(lines, start=1):
        matched = [name for name, pattern in SIGNAL_PATTERNS.items() if pattern.search(line)]
        if matched:
            hits.append({"line_number": idx, "signal_types": matched, "line": line})
        if len(hits) >= max_hits:
            break
    return hits


def _find_latest_session(logs_root: Path) -> Optional[Path]:
    if not logs_root.exists():
        return None
    sessions = [p for p in logs_root.iterdir() if p.is_dir()]
    if not sessions:
        return None
    sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return sessions[0]


def _find_named_session(logs_root: Path, session_id: str) -> Optional[Path]:
    p = logs_root / session_id
    if p.exists() and p.is_dir():
        return p
    return None


def _collect_extension_inventory() -> List[Dict[str, Any]]:
    ext_root = Path.home() / ".vscode" / "extensions"
    if not ext_root.exists():
        return []
    items: List[Dict[str, Any]] = []
    for d in sorted([p for p in ext_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        try:
            mtime = datetime.fromtimestamp(d.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        except OSError:
            mtime = "unknown"
        items.append({"name": d.name, "last_write_utc": mtime})
    return items


def _collect_crashpad(code_root: Path) -> Dict[str, Any]:
    crashpad = code_root / "Crashpad" / "reports"
    result: Dict[str, Any] = {"path": str(crashpad), "exists": crashpad.exists(), "reports": []}
    if not crashpad.exists():
        return result
    reports: List[Dict[str, Any]] = []
    for file in sorted([p for p in crashpad.iterdir() if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        try:
            mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            size = file.stat().st_size
        except OSError:
            mtime = "unknown"
            size = 0
        reports.append({"name": file.name, "bytes": size, "last_write_utc": mtime})
    result["reports"] = reports
    return result


def _resolve_paths(out_dir_arg: Optional[str]) -> AuditPaths:
    repo_root = Path(__file__).resolve().parents[3]
    day = _now_utc().strftime("%Y%m%d")
    default_out = repo_root / "report_tmp" / "audits" / day / "evidence"
    out_dir = Path(out_dir_arg).resolve() if out_dir_arg else default_out
    stamp = _stamp(_now_utc())
    json_path = out_dir / f"vscode_crash_audit_{stamp}.json"
    md_path = out_dir / f"vscode_crash_audit_{stamp}.md"
    return AuditPaths(repo_root=repo_root, out_dir=out_dir, json_path=json_path, md_path=md_path)


def _build_payload(session_dir: Path, max_tail_lines: int) -> Dict[str, Any]:
    window1 = session_dir / "window1"
    paths = {
        "main_log": session_dir / "main.log",
        "sharedprocess_log": session_dir / "sharedprocess.log",
        "ptyhost_log": session_dir / "ptyhost.log",
        "renderer_log": window1 / "renderer.log",
        "exthost_log": window1 / "exthost" / "exthost.log",
    }

    tails: Dict[str, List[str]] = {key: _read_tail(path, max_tail_lines) for key, path in paths.items()}
    combined: List[str] = []
    for key in ("main_log", "renderer_log", "exthost_log", "sharedprocess_log", "ptyhost_log"):
        combined.extend(tails.get(key, []))

    code_root = Path(os.environ.get("APPDATA", "")) / "Code"

    payload: Dict[str, Any] = {
        "generated_at": _now_utc().isoformat().replace("+00:00", "Z"),
        "session": {
            "path": str(session_dir),
            "id": session_dir.name,
        },
        "signals": _score_signals(combined),
        "signal_samples": _extract_signal_lines(combined),
        "tails": tails,
        "extensions": _collect_extension_inventory(),
        "crashpad": _collect_crashpad(code_root),
        "policy_context": {
            "script_first": True,
            "dry_run_supported": True,
            "names_only": True,
        },
    }
    return payload


def _render_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# VS Code Crash Audit — {payload.get('generated_at', 'unknown')}")
    lines.append("")
    session = payload.get("session", {})
    signals = payload.get("signals", {})
    lines.append("## Session")
    lines.append("")
    lines.append(f"- Session ID: `{session.get('id', 'unknown')}`")
    lines.append(f"- Session Path: `{session.get('path', 'unknown')}`")
    lines.append("")
    lines.append("## Signal counts")
    lines.append("")
    for key, value in signals.items():
        lines.append(f"- `{key}`: `{value}`")

    lines.append("")
    lines.append("## Signal samples")
    lines.append("")
    samples = payload.get("signal_samples", [])
    if not samples:
        lines.append("- No matching signal lines found in sampled tails.")
    else:
        lines.append("```text")
        for sample in samples[:40]:
            line_no = sample.get("line_number", "?")
            sigs = ",".join(sample.get("signal_types", []))
            line = sample.get("line", "")
            lines.append(f"[{line_no}] [{sigs}] {line}")
        lines.append("```")

    lines.append("")
    lines.append("## Extensions (inventory snapshot)")
    lines.append("")
    exts = payload.get("extensions", [])
    if not exts:
        lines.append("- No extension directories found.")
    else:
        for ext in exts[:120]:
            lines.append(f"- `{ext.get('name')}` (last_write_utc={ext.get('last_write_utc')})")

    crashpad = payload.get("crashpad", {})
    lines.append("")
    lines.append("## Crashpad reports")
    lines.append("")
    lines.append(f"- Path: `{crashpad.get('path', 'unknown')}`")
    lines.append(f"- Exists: `{crashpad.get('exists', False)}`")
    reports = crashpad.get("reports", []) if isinstance(crashpad, dict) else []
    if reports:
        for report in reports:
            lines.append(f"- `{report.get('name')}` bytes={report.get('bytes')} last_write_utc={report.get('last_write_utc')}")
    else:
        lines.append("- No crash reports discovered in sampled directory.")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Names-only evidence output; token redaction applied.")
    lines.append("- Use this output as crash-audit evidence before remediation actions.")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect VS Code crash-audit evidence.")
    parser.add_argument("--session-id", default=None, help="Optional VS Code log session ID (e.g., 20260219T104841).")
    parser.add_argument("--max-tail-lines", type=int, default=500, help="Max tail lines per log file (default: 500).")
    parser.add_argument("--out-dir", default=None, help="Optional output directory. Default: report_tmp/audits/<utc-day>/evidence")
    parser.add_argument("--dry-run", action="store_true", help="Collect + print summary only; do not write files.")
    parser.add_argument("--apply", action="store_true", help="Write JSON/MD artifacts to output directory.")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("[FAIL] Choose an explicit mode: --dry-run or --apply")
        return 2
    if args.dry_run and args.apply:
        print("[FAIL] Choose only one mode: --dry-run or --apply")
        return 2

    code_logs = Path(os.environ.get("APPDATA", "")) / "Code" / "logs"
    if not code_logs.exists():
        print(f"[FAIL] VS Code logs root not found: {code_logs}")
        return 3

    session_dir = _find_named_session(code_logs, args.session_id) if args.session_id else _find_latest_session(code_logs)
    if session_dir is None:
        print("[FAIL] No VS Code log session found.")
        return 4

    payload = _build_payload(session_dir=session_dir, max_tail_lines=max(50, args.max_tail_lines))

    signals = payload.get("signals", {})
    print(f"[OK] Session: {payload['session']['id']}")
    print("[OK] Signal summary:")
    for key, value in signals.items():
        print(f"  - {key}: {value}")

    if args.dry_run:
        print("[OK] Dry-run complete. No files written.")
        return 0

    paths = _resolve_paths(args.out_dir)
    paths.out_dir.mkdir(parents=True, exist_ok=True)

    paths.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    paths.md_path.write_text(_render_markdown(payload), encoding="utf-8")

    print(f"[OK] Wrote {paths.json_path}")
    print(f"[OK] Wrote {paths.md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
