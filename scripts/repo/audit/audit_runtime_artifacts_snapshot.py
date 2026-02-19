"""Audit runtime artifacts (heartbeats, telemetry, logs) using names-only evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_stat(path: Path) -> Tuple[bool, int, float]:
    try:
        st = path.stat()
        return True, int(st.st_size), float(st.st_mtime)
    except Exception:
        return False, 0, 0.0


def _age_s(mtime: float) -> Optional[float]:
    if not mtime:
        return None
    return max(0.0, time.time() - float(mtime))


def _sha256_tail(path: Path, max_bytes: int) -> str:
    try:
        size = int(path.stat().st_size)
        read_len = min(max_bytes, size)
        with path.open("rb") as f:
            if size > read_len:
                f.seek(size - read_len)
            data = f.read(read_len)
        return hashlib.sha256(data).hexdigest()
    except Exception:
        return ""


def _hb_status(exists: bool, age: Optional[float], warn_s: float, err_s: float) -> str:
    if not exists:
        return "ERR"
    if age is None:
        return "WARN"
    if age >= err_s:
        return "ERR"
    if age >= warn_s:
        return "WARN"
    return "OK"


def _parse_kv_arg(items: List[str], *, sep: str = "=") -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in items:
        if sep not in item:
            continue
        k, v = item.split(sep, 1)
        k = k.strip()
        v = v.strip()
        if k and v:
            out[k] = v
    return out


def _render_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# Runtime Artifacts Snapshot",
        "",
        f"- Created (UTC): {payload.get('created_at_utc','')}",
        f"- Runtime root: `{payload.get('runtime_root','')}`",
        "",
        "## Heartbeats",
        "",
    ]
    for row in payload.get("checks", {}).get("heartbeats", []):
        lines.append(f"- [{row.get('status')}] {row.get('name')}: exists={row.get('exists')} age_s={row.get('age_seconds')}")

    lines.extend(["", "## Telemetry files", ""])
    for row in payload.get("checks", {}).get("telemetry", []):
        lines.append(f"- {row.get('path')}: size_bytes={row.get('size_bytes')} age_s={row.get('age_seconds')}")

    lines.extend(["", "## Service logs", ""])
    for row in payload.get("checks", {}).get("service_logs", []):
        lines.append(f"- {row.get('path')}: exists={row.get('exists')} size_bytes={row.get('size_bytes')}")

    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Audit runtime artifacts and write names-only snapshot artifacts.")
    ap.add_argument("--runtime-root", type=Path, default=Path.cwd())
    ap.add_argument("--heartbeat", action="append", default=[], help="Heartbeat mapping NAME=relative/path")
    ap.add_argument("--telemetry-glob", action="append", default=["**/*.jsonl"], help="Glob relative to runtime root")
    ap.add_argument("--service-log-glob", action="append", default=["**/*.log"], help="Glob relative to runtime root")
    ap.add_argument("--max-tail-bytes", type=int, default=16384)
    ap.add_argument("--hb-warn-seconds", type=float, default=300.0)
    ap.add_argument("--hb-err-seconds", type=float, default=900.0)
    ap.add_argument("--out-dir", type=Path, default=Path("report_tmp/audits/runtime"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    root = args.runtime_root.resolve()
    hb_map = _parse_kv_arg(list(args.heartbeat or []))

    heartbeats: List[Dict[str, Any]] = []
    for name, rel in sorted(hb_map.items()):
        p = (root / rel).resolve()
        exists, size, mtime = _safe_stat(p)
        age = _age_s(mtime)
        heartbeats.append(
            {
                "name": name,
                "path": str(p),
                "exists": exists,
                "size_bytes": size,
                "age_seconds": None if age is None else round(age, 3),
                "status": _hb_status(exists, age, float(args.hb_warn_seconds), float(args.hb_err_seconds)),
            }
        )

    telemetry: List[Dict[str, Any]] = []
    seen_telemetry: set[str] = set()
    for g in list(args.telemetry_glob or []):
        for p in sorted(root.glob(g)):
            if not p.is_file():
                continue
            key = str(p.resolve())
            if key in seen_telemetry:
                continue
            seen_telemetry.add(key)
            exists, size, mtime = _safe_stat(p)
            age = _age_s(mtime)
            telemetry.append(
                {
                    "path": str(p),
                    "exists": exists,
                    "size_bytes": size,
                    "age_seconds": None if age is None else round(age, 3),
                    "sha256_tail": _sha256_tail(p, int(args.max_tail_bytes)),
                }
            )

    service_logs: List[Dict[str, Any]] = []
    seen_logs: set[str] = set()
    for g in list(args.service_log_glob or []):
        for p in sorted(root.glob(g)):
            if not p.is_file():
                continue
            key = str(p.resolve())
            if key in seen_logs:
                continue
            seen_logs.add(key)
            exists, size, mtime = _safe_stat(p)
            age = _age_s(mtime)
            service_logs.append(
                {
                    "path": str(p),
                    "exists": exists,
                    "size_bytes": size,
                    "age_seconds": None if age is None else round(age, 3),
                    "sha256_tail": _sha256_tail(p, int(args.max_tail_bytes)),
                }
            )

    payload = {
        "created_at_utc": _utc_now(),
        "runtime_root": str(root),
        "checks": {
            "heartbeats": heartbeats,
            "telemetry": telemetry,
            "service_logs": service_logs,
        },
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = datetime.now(timezone.utc).strftime("runtime_artifacts_snapshot_%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_md(payload), encoding="utf-8")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
