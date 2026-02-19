"""VS Code crash remediation triage.

Consumes crash-audit evidence and optional process-attribution artifacts,
then emits prioritized recommendations. Can optionally apply low-risk
workspace tuning settings.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _latest_file(glob_pattern: str, base: Path) -> Optional[Path]:
    files = sorted(base.glob(glob_pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _load_json(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        text_sig = path.read_text(encoding="utf-8-sig", errors="replace")
        return json.loads(text_sig)


def _coerce_bool(value: Any) -> bool:
    return bool(value)


def _assess_pylance_pressure(attribution: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    rows = attribution.get("rows", [])
    suspects: List[Dict[str, Any]] = []
    for row in rows:
        cmd = str(row.get("Cmd", ""))
        ws_mb = float(row.get("WS_MB", 0) or 0)
        if "vscode-pylance" in cmd.lower() and ws_mb >= 800:
            suspects.append(
                {
                    "pid": row.get("PID"),
                    "ws_mb": ws_mb,
                    "cmd": cmd,
                    "name": row.get("Name"),
                }
            )
    return (len(suspects) > 0, suspects)


def _build_recommendations(signals: Dict[str, Any], pylance_hot: bool) -> List[str]:
    listener = int(signals.get("listener_leak", 0) or 0)
    unresp = int(signals.get("extension_unresponsive", 0) or 0)
    uri_err = int(signals.get("uri_error", 0) or 0)

    recs: List[str] = []
    if listener >= 10:
        recs.append("High listener leak pressure detected; prioritize extension-host load shedding and extension cohort isolation.")
    if unresp > 0:
        recs.append("Extension host unresponsive events detected; run a minimal-extension workspace profile until stabilized.")
    if pylance_hot:
        recs.append("Pylance memory pressure detected; switch Python analysis to open-files mode and disable indexing during recovery.")
    if uri_err > 0:
        recs.append("URI parsing errors observed; validate URI-producing extensions/workspace links during batch isolation.")

    recs.append("Re-run crash audit after each change and compare signal counts to verify improvements.")
    return recs


def _workspace_tuning_patch(settings: Dict[str, Any]) -> Dict[str, Any]:
    settings["python.analysis.diagnosticMode"] = "openFilesOnly"
    settings["python.analysis.indexing"] = False
    settings["python.analysis.userFileIndexingLimit"] = 2000

    watcher = settings.get("files.watcherExclude", {})
    if not isinstance(watcher, dict):
        watcher = {}
    watcher["**/.venv/**"] = True
    watcher["**/.venv-core/**"] = True
    settings["files.watcherExclude"] = watcher

    search_ex = settings.get("search.exclude", {})
    if not isinstance(search_ex, dict):
        search_ex = {}
    search_ex["**/.venv/**"] = True
    search_ex["**/.venv-core/**"] = True
    settings["search.exclude"] = search_ex

    files_ex = settings.get("files.exclude", {})
    if not isinstance(files_ex, dict):
        files_ex = {}
    files_ex["**/.venv/**"] = True
    files_ex["**/.venv-core/**"] = True
    settings["files.exclude"] = files_ex

    return settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate VS Code crash remediation triage from evidence.")
    parser.add_argument("--dry-run", action="store_true", help="Read evidence and print triage summary only.")
    parser.add_argument("--apply", action="store_true", help="Write triage JSON/MD artifact files.")
    parser.add_argument("--crash-evidence", type=Path, default=None, help="Optional explicit crash audit JSON input.")
    parser.add_argument(
        "--attribution-dir",
        type=Path,
        default=None,
        help="Optional directory containing process attribution JSON files (vscode_process_attribution_*.json).",
    )
    parser.add_argument(
        "--apply-workspace-tuning",
        action="store_true",
        help="Apply safe workspace settings tuning (.vscode/settings.json). Requires --apply.",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("[FAIL] Choose an explicit mode: --dry-run or --apply")
        return 2
    if args.dry_run and args.apply:
        print("[FAIL] Choose only one mode: --dry-run or --apply")
        return 2
    if args.apply_workspace_tuning and not args.apply:
        print("[FAIL] --apply-workspace-tuning requires --apply")
        return 2

    root = _repo_root()
    day = _now().strftime("%Y%m%d")
    evidence_dir = root / "report_tmp" / "audits" / day / "evidence"

    crash_json = args.crash_evidence.resolve() if args.crash_evidence else _latest_file("vscode_crash_audit_*.json", evidence_dir)
    if crash_json is None or (not crash_json.exists()):
        print(f"[FAIL] No crash audit JSON found under {evidence_dir}")
        return 3

    crash = _load_json(crash_json)
    signals = crash.get("signals", {})

    attr_dir = args.attribution_dir.resolve() if args.attribution_dir else (root / "report_tmp" / "process_attribution")
    attr_json = _latest_file("vscode_process_attribution_*.json", attr_dir) if attr_dir.exists() else None
    attribution = _load_json(attr_json) if attr_json else {"rows": []}

    pylance_hot, pylance_suspects = _assess_pylance_pressure(attribution)
    recommendations = _build_recommendations(signals=signals, pylance_hot=pylance_hot)

    summary: Dict[str, Any] = {
        "generated_at": _now().isoformat().replace("+00:00", "Z"),
        "crash_audit_source": str(crash_json),
        "attribution_source": str(attr_json) if attr_json else None,
        "signals": signals,
        "pylance_memory_pressure": _coerce_bool(pylance_hot),
        "pylance_suspects": pylance_suspects,
        "recommendations": recommendations,
        "workspace_tuning_applied": False,
    }

    print("[OK] Triage summary")
    print(f"  - crash source: {crash_json.name}")
    print(f"  - attribution source: {attr_json.name if attr_json else 'none'}")
    print(f"  - listener_leak: {signals.get('listener_leak', 0)}")
    print(f"  - extension_unresponsive: {signals.get('extension_unresponsive', 0)}")
    print(f"  - pylance_memory_pressure: {pylance_hot}")

    if args.dry_run:
        for idx, rec in enumerate(recommendations, start=1):
            print(f"  {idx}. {rec}")
        print("[OK] Dry-run complete. No files written.")
        return 0

    evidence_dir.mkdir(parents=True, exist_ok=True)
    out_stamp = _stamp(_now())
    out_json = evidence_dir / f"vscode_crash_remediation_triage_{out_stamp}.json"
    out_md = evidence_dir / f"vscode_crash_remediation_triage_{out_stamp}.md"

    if args.apply_workspace_tuning:
        settings_path = root / ".vscode" / "settings.json"
        settings: Dict[str, Any] = {}
        if settings_path.exists():
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings = _workspace_tuning_patch(settings)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        summary["workspace_tuning_applied"] = True
        summary["workspace_settings_path"] = str(settings_path)

    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_lines: List[str] = []
    md_lines.append(f"# VS Code Crash Remediation Triage — {summary['generated_at']}")
    md_lines.append("")
    md_lines.append("## Inputs")
    md_lines.append("")
    md_lines.append(f"- Crash evidence: `{summary['crash_audit_source']}`")
    md_lines.append(f"- Attribution evidence: `{summary['attribution_source']}`")
    md_lines.append("")
    md_lines.append("## Signal summary")
    md_lines.append("")
    for key, value in summary["signals"].items():
        md_lines.append(f"- `{key}`: `{value}`")
    md_lines.append(f"- `pylance_memory_pressure`: `{summary['pylance_memory_pressure']}`")
    md_lines.append("")
    if pylance_suspects:
        md_lines.append("## Pylance high-memory suspects")
        md_lines.append("")
        for s in pylance_suspects:
            md_lines.append(f"- pid={s.get('pid')} ws_mb={s.get('ws_mb')} name={s.get('name')}")
        md_lines.append("")
    md_lines.append("## Prioritized recommendations")
    md_lines.append("")
    for idx, rec in enumerate(summary["recommendations"], start=1):
        md_lines.append(f"{idx}. {rec}")
    md_lines.append("")
    md_lines.append(f"- workspace_tuning_applied: `{summary['workspace_tuning_applied']}`")
    if summary.get("workspace_settings_path"):
        md_lines.append(f"- workspace_settings_path: `{summary['workspace_settings_path']}`")

    out_md.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")

    print(f"[OK] Wrote {out_json}")
    print(f"[OK] Wrote {out_md}")
    if summary["workspace_tuning_applied"]:
        print(f"[OK] Applied workspace tuning at {summary['workspace_settings_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
