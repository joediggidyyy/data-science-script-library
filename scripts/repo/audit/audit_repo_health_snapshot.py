"""Audit repository hygiene and emit a names-only snapshot."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(cmd: Sequence[str], cwd: Path) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(list(cmd), cwd=str(cwd), capture_output=True, text=True, check=False)
        return int(p.returncode), str(p.stdout or ""), str(p.stderr or "")
    except Exception as e:
        return 999, "", repr(e)


def _git_ls_files(repo_root: Path) -> List[str]:
    rc, out, _ = _run(["git", "ls-files"], cwd=repo_root)
    if rc != 0:
        return []
    return [x.strip().replace("\\", "/") for x in out.splitlines() if x.strip()]


def _git_check_ignore(repo_root: Path, rel_path: str) -> Optional[bool]:
    rc, _, _ = _run(["git", "check-ignore", "-q", "--", rel_path], cwd=repo_root)
    if rc == 0:
        return True
    if rc == 1:
        return False
    return None


def _render_md(payload: Dict[str, Any]) -> str:
    c = payload.get("checks", {})
    lines = [
        "# Repo Health Snapshot",
        "",
        f"- Created (UTC): {payload.get('created_at_utc','')}",
        f"- Repo root: `{payload.get('repo_root','')}`",
        f"- Tracked files scanned: {c.get('tracked_file_count', 0)}",
        "",
        "## Findings",
        "",
    ]
    tracked_bad = c.get("tracked_should_not_be_tracked", [])
    ignore_bad = c.get("ignore_policy_violations", [])
    lines.append(f"- tracked_should_not_be_tracked: {len(tracked_bad)}")
    lines.append(f"- ignore_policy_violations: {len(ignore_bad)}")
    if tracked_bad:
        lines.extend(["", "### Tracked paths flagged", ""])
        for p in tracked_bad[:100]:
            lines.append(f"- `{p}`")
    if ignore_bad:
        lines.extend(["", "### Ignore policy violations", ""])
        for p in ignore_bad[:100]:
            lines.append(f"- `{p}`")
    lines.append("")
    return "\n".join(lines)


def audit_repo_health(
    repo_root: Path,
    *,
    deny_contains: List[str],
    deny_exts: List[str],
    expect_ignored: List[str],
) -> Dict[str, Any]:
    tracked = _git_ls_files(repo_root)
    flagged: List[str] = []
    for p in tracked:
        p_l = p.lower()
        if any(s.lower() in p_l for s in deny_contains):
            flagged.append(p)
            continue
        if any(p_l.endswith(ext.lower()) for ext in deny_exts):
            flagged.append(p)

    ignore_viol = []
    for rel in expect_ignored:
        ok = _git_check_ignore(repo_root, rel)
        if ok is False:
            ignore_viol.append(rel)

    return {
        "tracked_file_count": len(tracked),
        "tracked_should_not_be_tracked": flagged,
        "ignore_policy_violations": ignore_viol,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Audit repository hygiene and emit snapshot artifacts.")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--out-dir", type=Path, default=Path("report_tmp/audits/repo_health"))
    ap.add_argument("--deny-contains", action="append", default=["/local_untracked/", "/logs/", "/archive/"])
    ap.add_argument("--deny-ext", action="append", default=[".log", ".jsonl", ".sqlite", ".db", ".pid", ".key", ".pem"])
    ap.add_argument("--expect-ignored", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    repo_root = args.repo_root.resolve()
    checks = audit_repo_health(
        repo_root,
        deny_contains=list(args.deny_contains or []),
        deny_exts=list(args.deny_ext or []),
        expect_ignored=list(args.expect_ignored or []),
    )

    payload = {
        "created_at_utc": _utc_now(),
        "repo_root": str(repo_root),
        "checks": checks,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = datetime.now(timezone.utc).strftime("repo_health_snapshot_%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_md(payload), encoding="utf-8")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
