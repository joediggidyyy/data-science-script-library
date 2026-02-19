"""Generate a names-only runtime parameters report (env surface + path checks)."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_stat(path: Path) -> Dict[str, Any]:
    try:
        st = path.stat()
        age = max(0.0, time.time() - float(st.st_mtime))
        return {
            "exists": True,
            "size_bytes": int(st.st_size),
            "age_seconds": round(age, 3),
        }
    except Exception:
        return {
            "exists": False,
            "size_bytes": 0,
            "age_seconds": None,
        }


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _render_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# Runtime Parameters Report",
        "",
        f"- Created (UTC): {payload.get('created_at_utc','')}",
        f"- Runtime root: `{payload.get('runtime_root','')}`",
        "",
        "## Environment (names-only)",
        "",
    ]
    for k, v in sorted((payload.get("env", {}) or {}).items()):
        lines.append(f"- {k}: {'set' if v else 'not set'}")

    lines.extend(["", "## Path safety", ""])
    ps = payload.get("path_safety", {}) or {}
    for k, v in sorted(ps.items()):
        if isinstance(v, bool):
            lines.append(f"- {k}: {v}")

    lines.extend(["", "## Filesystem checks", ""])
    for row in payload.get("files", []):
        lines.append(f"- {row.get('path')}: exists={row.get('exists')} size_bytes={row.get('size_bytes')} age_s={row.get('age_seconds')}")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Generate runtime parameter report with names-only output.")
    ap.add_argument("--runtime-root", type=Path, default=Path.cwd())
    ap.add_argument("--env-name", action="append", default=[])
    ap.add_argument("--check-path", action="append", default=[], help="Relative file/dir paths to stat")
    ap.add_argument("--out-dir", type=Path, default=Path("report_tmp/reports/runtime_parameters"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    root = args.runtime_root.resolve()
    env = {name: bool(os.getenv(name)) for name in list(args.env_name or [])}

    rows: List[Dict[str, Any]] = []
    for rel in list(args.check_path or []):
        p = (root / rel).resolve()
        st = _safe_stat(p)
        rows.append({"path": str(p), **st})

    payload = {
        "created_at_utc": _utc_now(),
        "runtime_root": str(root),
        "env": env,
        "files": rows,
        "path_safety": {
            "all_checks_within_runtime_root": all(_is_within(Path(r["path"]), root) for r in rows),
        },
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = datetime.now(timezone.utc).strftime("runtime_parameters_report_%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_md(payload), encoding="utf-8")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
