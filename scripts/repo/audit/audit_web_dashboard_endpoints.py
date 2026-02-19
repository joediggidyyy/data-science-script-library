"""Audit web dashboard endpoints and produce names-only evidence artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _http_get(url: str, timeout: float = 3.5) -> Dict[str, Any]:
    req = Request(url, headers={"User-Agent": "dsl-web-audit/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read() or b""
            return {
                "ok": 200 <= int(getattr(resp, "status", 200)) < 300,
                "status": int(getattr(resp, "status", 200)),
                "content_type": str(resp.headers.get("Content-Type") or ""),
                "body_len": len(body),
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "error": "",
            }
    except HTTPError as e:
        return {"ok": False, "status": int(getattr(e, "code", 0) or 0), "content_type": "", "body_len": 0, "body_sha256": "", "error": repr(e)}
    except URLError as e:
        return {"ok": False, "status": 0, "content_type": "", "body_len": 0, "body_sha256": "", "error": repr(e)}
    except Exception as e:
        return {"ok": False, "status": 0, "content_type": "", "body_len": 0, "body_sha256": "", "error": repr(e)}


def _tcp_probe(host: str, port: int, timeout: float = 1.5) -> Dict[str, Any]:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return {"ok": True, "detail": "ok"}
    except Exception as e:
        return {"ok": False, "detail": repr(e)}


def _render_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# Web Dashboard Endpoint Audit",
        "",
        f"- Created (UTC): {payload.get('created_at_utc','')}",
        f"- Base URL: `{payload.get('base_url','')}`",
        f"- TCP probe: {payload.get('tcp_probe',{}).get('ok')}",
        "",
        "## Endpoint checks",
        "",
    ]
    for ep, row in sorted((payload.get("endpoints", {}) or {}).items()):
        lines.append(f"- `{ep}` status={row.get('status')} ok={row.get('ok')} body_len={row.get('body_len')} sha256={row.get('body_sha256')}")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Audit web dashboard endpoints.")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--endpoint", action="append", default=["/"], help="Relative endpoint path (repeatable)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=80)
    ap.add_argument("--out-dir", type=Path, default=Path("report_tmp/audits/web_dashboard"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    base = str(args.base_url).rstrip("/")
    endpoints: Dict[str, Dict[str, Any]] = {}
    for ep in list(args.endpoint or []):
        rel = ep if ep.startswith("/") else f"/{ep}"
        endpoints[rel] = _http_get(f"{base}{rel}")

    payload = {
        "created_at_utc": _utc_now(),
        "base_url": base,
        "tcp_probe": _tcp_probe(str(args.host), int(args.port)),
        "endpoints": endpoints,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = datetime.now(timezone.utc).strftime("web_dashboard_audit_%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_md(payload), encoding="utf-8")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
