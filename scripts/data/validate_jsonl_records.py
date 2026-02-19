"""Validate JSONL records with configurable key and signature policies.

This validator is intentionally stdlib-only and names-only.
"""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_jsonl(path: Path, max_lines: Optional[int] = None) -> Tuple[int, Optional[Dict[str, Any]], Optional[str]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, raw in enumerate(f, start=1):
            if max_lines is not None and line_no > max_lines:
                break
            s = raw.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception as e:
                yield line_no, None, f"json_parse_error:{e.__class__.__name__}"
                continue
            if not isinstance(obj, dict):
                yield line_no, None, "record_not_object"
                continue
            yield line_no, obj, None


def _parse_csv_set(raw: Optional[str]) -> Set[str]:
    if not raw:
        return set()
    return {x.strip() for x in raw.split(",") if x.strip()}


def _load_signature_verifier(spec: Optional[str]) -> Optional[Callable[[Dict[str, Any]], bool]]:
    if not spec:
        return None
    if ":" not in spec:
        raise ValueError("--signature-verifier must be module:function")
    module_name, fn_name = spec.split(":", 1)
    mod = importlib.import_module(module_name)
    fn = getattr(mod, fn_name)
    if not callable(fn):
        raise ValueError("signature verifier target is not callable")
    return fn


@dataclass
class ValidationSummary:
    input_path: str
    created_at_utc: str
    total_lines: int
    ok_records: int
    error_lines: int
    forbidden_key_hits: int
    unknown_keys: int
    unknown_keys_examples: List[str]
    signature_present: int
    signature_verified: int
    signature_failed: int


def validate_jsonl_records(
    input_path: Path,
    *,
    allowed_keys: Optional[Set[str]] = None,
    forbidden_keys: Optional[Set[str]] = None,
    strict_unknown_keys: bool = False,
    verify_signatures: bool = False,
    signature_key: str = "signature",
    signature_verifier: Optional[Callable[[Dict[str, Any]], bool]] = None,
    max_lines: Optional[int] = None,
) -> Tuple[ValidationSummary, List[str]]:
    errors: List[str] = []
    unknown_examples: List[str] = []
    total = ok = err = 0
    forbidden_hits = unknown_hits = 0
    sig_present = sig_verified = sig_failed = 0

    for line_no, rec, parse_err in _iter_jsonl(input_path, max_lines=max_lines):
        total += 1
        if parse_err is not None or rec is None:
            err += 1
            errors.append(f"{input_path.name}:{line_no}:{parse_err}")
            continue

        if forbidden_keys:
            found = sorted([k for k in rec.keys() if k in forbidden_keys])
            if found:
                forbidden_hits += len(found)
                err += 1
                errors.append(f"{input_path.name}:{line_no}:forbidden_keys={','.join(found)}")
                continue

        if allowed_keys is not None:
            extra = sorted([k for k in rec.keys() if k not in allowed_keys])
            if extra:
                unknown_hits += len(extra)
                for key in extra:
                    if len(unknown_examples) < 10 and key not in unknown_examples:
                        unknown_examples.append(key)
                if strict_unknown_keys:
                    err += 1
                    errors.append(f"{input_path.name}:{line_no}:unknown_keys={','.join(extra[:5])}")
                    continue

        if signature_key in rec:
            sig_present += 1
            if verify_signatures:
                if signature_verifier is None:
                    sig_failed += 1
                    err += 1
                    errors.append(f"{input_path.name}:{line_no}:signature_verifier_missing")
                    continue
                try:
                    if bool(signature_verifier(rec)):
                        sig_verified += 1
                    else:
                        sig_failed += 1
                        err += 1
                        errors.append(f"{input_path.name}:{line_no}:signature_invalid")
                        continue
                except Exception:
                    sig_failed += 1
                    err += 1
                    errors.append(f"{input_path.name}:{line_no}:signature_check_error")
                    continue

        ok += 1

    summary = ValidationSummary(
        input_path=str(input_path),
        created_at_utc=_utc_now_iso(),
        total_lines=total,
        ok_records=ok,
        error_lines=err,
        forbidden_key_hits=forbidden_hits,
        unknown_keys=unknown_hits,
        unknown_keys_examples=sorted(unknown_examples),
        signature_present=sig_present,
        signature_verified=sig_verified,
        signature_failed=sig_failed,
    )
    return summary, errors


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Validate JSONL records with configurable policies.")
    ap.add_argument("--input", required=True, type=Path, help="Path to input JSONL")
    ap.add_argument("--allowed-keys", default=None, help="Comma-separated allowlist keys")
    ap.add_argument("--forbidden-keys", default="content,message,text,body,prompt,system_prompt,raw", help="Comma-separated forbidden keys")
    ap.add_argument("--strict-unknown-keys", action="store_true", help="Fail on unknown keys")
    ap.add_argument("--verify-signatures", action="store_true", help="Verify records containing signature key")
    ap.add_argument("--signature-key", default="signature", help="Signature field name")
    ap.add_argument("--signature-verifier", default=None, help="Verifier in module:function format")
    ap.add_argument("--max-lines", type=int, default=None, help="Optional max line count")
    ap.add_argument("--json", action="store_true", help="Emit summary as JSON")
    args = ap.parse_args(argv)

    verifier: Optional[Callable[[Dict[str, Any]], bool]] = None
    if args.verify_signatures:
        try:
            verifier = _load_signature_verifier(args.signature_verifier)
        except Exception as e:
            print(f"Error: could not load signature verifier: {e}")
            return 2

    allowed: Optional[Set[str]] = _parse_csv_set(args.allowed_keys) if args.allowed_keys else None
    forbidden = _parse_csv_set(args.forbidden_keys)

    summary, errors = validate_jsonl_records(
        args.input,
        allowed_keys=allowed,
        forbidden_keys=forbidden,
        strict_unknown_keys=bool(args.strict_unknown_keys),
        verify_signatures=bool(args.verify_signatures),
        signature_key=str(args.signature_key),
        signature_verifier=verifier,
        max_lines=args.max_lines,
    )

    if args.json:
        print(json.dumps({"summary": asdict(summary), "errors": errors[:100]}, indent=2, sort_keys=True))
    else:
        print(f"[validate_jsonl_records] input={args.input.name} ok={summary.ok_records} errors={summary.error_lines}")
        for e in errors[:20]:
            print(f"  - {e}")
        if len(errors) > 20:
            print(f"  ... ({len(errors) - 20} more)")

    return 0 if summary.error_lines == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
