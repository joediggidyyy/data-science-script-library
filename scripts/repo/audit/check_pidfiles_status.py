"""Check process status from PID files.

Names-only output. Reads PID values and reports running/not-running status.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
except Exception:
    psutil = None


def _read_pid(path: Path) -> Optional[int]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
        if raw.isdigit():
            return int(raw)
    except Exception:
        return None
    return None


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Check status of processes referenced by pidfiles.")
    ap.add_argument("--pidfile", action="append", required=True, help="PID file mapping name=path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if psutil is None:
        print("Error: psutil is required for this script")
        return 2

    rows: List[Dict[str, Any]] = []
    for item in list(args.pidfile or []):
        if "=" not in item:
            continue
        name, p = item.split("=", 1)
        name = name.strip()
        path = Path(p.strip()).resolve()

        if not path.exists():
            rows.append({"name": name, "pidfile": str(path), "status": "pidfile_missing"})
            continue

        pid = _read_pid(path)
        if pid is None:
            rows.append({"name": name, "pidfile": str(path), "status": "pidfile_unreadable"})
            continue

        running = bool(psutil.pid_exists(pid))
        out: Dict[str, Any] = {"name": name, "pidfile": str(path), "pid": pid, "running": running}
        if running:
            try:
                p_obj = psutil.Process(pid)
                with p_obj.oneshot():
                    out["process_name"] = p_obj.name()
                    out["status"] = p_obj.status()
                    out["rss_bytes"] = int(p_obj.memory_info().rss)
            except Exception:
                out["status"] = "running_details_unavailable"
        else:
            out["status"] = "pid_not_running"
        rows.append(out)

    if args.json:
        print(json.dumps({"results": rows}, indent=2, sort_keys=True))
    else:
        for r in rows:
            name = r.get("name")
            status = r.get("status")
            pid = r.get("pid")
            if pid is None:
                print(f"{name}: {status}")
            else:
                print(f"{name}: pid={pid} status={status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
