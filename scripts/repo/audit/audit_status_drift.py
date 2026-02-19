"""Audit status drift between task SSOT, dashboard view, and task documents."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm_status(raw: str) -> str:
    v = (raw or "").strip().lower()
    v = v.replace("`", "").replace("*", "")
    v = re.sub(r"[^a-z0-9\-\s]", " ", v)
    v = re.sub(r"\s+", " ", v).strip().replace(" ", "-")
    v = re.sub(r"-+", "-", v)
    if v in {"", "unknown", "na", "n-a"}:
        return ""
    if v in {"active", "in-progress", "inprogress", "doing", "running"}:
        return "in-progress"
    if v in {"planned", "plan", "todo", "open", "opened", "pending", "queued", "backlog", "draft"}:
        return "open"
    if v in {"paused", "blocked", "stuck", "on-hold"}:
        return "blocked"
    if v in {"done", "closed", "complete", "completed"}:
        return "completed"
    return v


def _extract_status_from_md(text: str) -> str:
    pats = [
        r"\*\*Status\*\*\s*:\s*([^\n\r]+)",
        r"^\-\s*Status\s*:\s*`([^`]+)`",
        r"^\-\s*Status\s*:\s*([^\n\r]+)",
    ]
    for pat in pats:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return _norm_status((m.group(1) or "").strip().rstrip(" ."))
    return ""


def _load_tasks(path: Path) -> List[Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8", errors="ignore") or "[]")
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


def _load_dashboard_status(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    text = path.read_text(encoding="utf-8", errors="ignore")
    for ln in text.splitlines():
        if not ln.startswith("|"):
            continue
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        if len(parts) < 6:
            continue
        task_id = parts[0]
        status = _norm_status(parts[5])
        if task_id:
            out[task_id] = status
    return out


def _render_md(payload: Dict[str, Any]) -> str:
    viol = payload.get("violations", [])
    lines = [
        "# Status Drift Audit",
        "",
        f"- Created (UTC): {payload.get('created_at_utc','')}",
        f"- Checked tasks: {payload.get('checked_task_count', 0)}",
        f"- Violations: {len(viol)}",
        "",
        "## Violations",
        "",
    ]
    if not viol:
        lines.append("- (none)")
    else:
        for v in viol[:200]:
            lines.append(
                f"- {v.get('task_id','?')}: expected={v.get('expected','?')} found={v.get('found','?')} source={v.get('source','?')} reason={v.get('reason','?')}"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Audit status drift between tasks, dashboard, and task docs.")
    ap.add_argument("--tasks-json", required=True, type=Path)
    ap.add_argument("--dashboard-md", type=Path, default=None)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--out-dir", type=Path, default=Path("report_tmp/audits/status_drift"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    repo_root = args.repo_root.resolve()
    tasks = _load_tasks(args.tasks_json.resolve())
    dash = _load_dashboard_status(args.dashboard_md.resolve()) if args.dashboard_md else {}

    violations: List[Dict[str, str]] = []
    checked = 0
    for t in tasks:
        task_id = str(t.get("id") or "").strip()
        t_path = str(t.get("path") or "").replace("\\", "/")
        expected = _norm_status(str(t.get("status") or ""))
        if not task_id or not t_path or not expected:
            continue
        checked += 1

        dash_found = dash.get(task_id)
        if dash_found and dash_found != expected:
            violations.append(
                {
                    "task_id": task_id,
                    "expected": expected,
                    "found": dash_found,
                    "source": "dashboard",
                    "reason": "dashboard status mismatch",
                }
            )

        task_doc = (repo_root / t_path).resolve()
        if not task_doc.exists() or not task_doc.is_file():
            violations.append(
                {
                    "task_id": task_id,
                    "expected": expected,
                    "found": "(missing)",
                    "source": t_path,
                    "reason": "task document missing",
                }
            )
            continue

        found = _extract_status_from_md(task_doc.read_text(encoding="utf-8", errors="ignore"))
        if not found:
            violations.append(
                {
                    "task_id": task_id,
                    "expected": expected,
                    "found": "(missing)",
                    "source": t_path,
                    "reason": "status field missing",
                }
            )
        elif found != expected:
            violations.append(
                {
                    "task_id": task_id,
                    "expected": expected,
                    "found": found,
                    "source": t_path,
                    "reason": "task document status mismatch",
                }
            )

    payload = {
        "created_at_utc": _utc_now(),
        "repo_root": str(repo_root),
        "checked_task_count": checked,
        "violations": violations,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = datetime.now(timezone.utc).strftime("status_drift_audit_%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_md(payload), encoding="utf-8")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
