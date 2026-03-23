#!/usr/bin/env python3
"""Extract text from one PDF or a directory of PDFs with best-effort backends.

This utility keeps PDF extraction optional and lightweight:
- try common backends if they are available,
- do not auto-install dependencies,
- write deterministic text artifacts and an optional manifest.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _extract_with_pypdf(pdf_path: Path, max_pages: Optional[int]) -> str:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(pdf_path))
    pages = reader.pages if max_pages is None else reader.pages[: max(0, int(max_pages))]
    return "\n\n".join((page.extract_text() or "") for page in pages)


def _extract_with_pypdf2(pdf_path: Path, max_pages: Optional[int]) -> str:
    from PyPDF2 import PdfReader  # type: ignore

    reader = PdfReader(str(pdf_path))
    pages = reader.pages if max_pages is None else reader.pages[: max(0, int(max_pages))]
    return "\n\n".join((page.extract_text() or "") for page in pages)


def _extract_with_pymupdf(pdf_path: Path, max_pages: Optional[int]) -> str:
    import fitz  # type: ignore

    doc = fitz.open(str(pdf_path))
    try:
        limit = len(doc) if max_pages is None else min(len(doc), max(0, int(max_pages)))
        return "\n\n".join((doc[i].get_text("text") or "") for i in range(limit))
    finally:
        doc.close()


def _extract_with_pdfminer(pdf_path: Path, max_pages: Optional[int]) -> str:
    from pdfminer.high_level import extract_text  # type: ignore

    page_numbers = None
    if max_pages is not None:
        page_numbers = list(range(max(0, int(max_pages))))
    return extract_text(str(pdf_path), page_numbers=page_numbers)


BackendFn = Callable[[Path, Optional[int]], str]

_BACKENDS: Tuple[Tuple[str, BackendFn], ...] = (
    ("pypdf", _extract_with_pypdf),
    ("PyPDF2", _extract_with_pypdf2),
    ("PyMuPDF(fitz)", _extract_with_pymupdf),
    ("pdfminer.six", _extract_with_pdfminer),
)


@dataclass(frozen=True)
class ExtractResult:
    input_pdf: str
    output_txt: str
    backend: str
    ok: bool
    chars_written: int
    error: Optional[str] = None


def extract_text_best_effort(pdf_path: Path, *, max_pages: Optional[int] = None) -> Tuple[str, str]:
    """Return `(backend_name, extracted_text)` using the first available backend."""

    last_err: Optional[BaseException] = None
    for name, fn in _BACKENDS:
        try:
            return name, fn(pdf_path, max_pages)
        except ModuleNotFoundError as e:
            last_err = e
            continue
        except Exception as e:  # pragma: no cover
            last_err = e
            continue

    tried = ", ".join(name for name, _ in _BACKENDS)
    raise RuntimeError(
        "No supported PDF extraction backend is available in this Python environment. "
        f"Tried: {tried}. Last error: {last_err}"
    )


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def _default_single_out(pdf_path: Path) -> Path:
    return pdf_path.with_name(pdf_path.stem + ".extracted.txt")


def _trim_text(text: str, *, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[TRUNCATED]\n"
    return text


def _write_extracted_text(output_path: Path, *, backend: str, pdf_path: Path, text: str) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = f"[extracted_with]={backend}\n[input_pdf]={pdf_path.as_posix()}\n\n"
    payload = header + text
    output_path.write_text(payload, encoding="utf-8", errors="replace")
    return len(text)


def extract_single_pdf(
    pdf_path: Path,
    *,
    output_path: Path,
    max_pages: Optional[int],
    max_chars: int,
) -> ExtractResult:
    try:
        backend, text = extract_text_best_effort(pdf_path, max_pages=max_pages)
        trimmed = _trim_text(text, max_chars=max_chars)
        chars_written = _write_extracted_text(output_path, backend=backend, pdf_path=pdf_path, text=trimmed)
        return ExtractResult(
            input_pdf=str(pdf_path).replace("\\", "/"),
            output_txt=str(output_path).replace("\\", "/"),
            backend=backend,
            ok=True,
            chars_written=chars_written,
        )
    except Exception as e:
        return ExtractResult(
            input_pdf=str(pdf_path).replace("\\", "/"),
            output_txt=str(output_path).replace("\\", "/"),
            backend="",
            ok=False,
            chars_written=0,
            error=f"{type(e).__name__}: {e}",
        )


def extract_pdf_directory(
    input_dir: Path,
    *,
    output_dir: Path,
    max_pages: Optional[int],
    max_chars: int,
) -> list[ExtractResult]:
    results: list[ExtractResult] = []
    for pdf_path in sorted(input_dir.rglob("*.pdf")):
        rel = _safe_rel(pdf_path, input_dir)
        safe_name = rel.replace("/", "__")
        out_txt = output_dir / f"{safe_name}.extracted.txt"
        results.append(
            extract_single_pdf(
                pdf_path,
                output_path=out_txt,
                max_pages=max_pages,
                max_chars=max_chars,
            )
        )
    return results


def _write_manifest(manifest_path: Path, payload: dict) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract text from one PDF or a directory of PDFs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf", help="Path to a single input PDF")
    group.add_argument("--input-dir", help="Directory containing PDFs to extract")

    parser.add_argument("--out", help="Output .txt path for single-PDF mode")
    parser.add_argument("--output-dir", help="Output directory for batch mode")
    parser.add_argument("--write-manifest", action="store_true", help="Write a JSON manifest of extraction results")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional maximum pages to extract per PDF")
    parser.add_argument("--max-chars", type=int, default=2_000_000, help="Maximum chars per extracted text payload")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.pdf:
        pdf_path = Path(args.pdf).resolve()
        if not pdf_path.exists():
            raise SystemExit(f"PDF not found: {pdf_path}")

        output_path = Path(args.out).resolve() if args.out else _default_single_out(pdf_path)
        result = extract_single_pdf(
            pdf_path,
            output_path=output_path,
            max_pages=args.max_pages,
            max_chars=max(1, int(args.max_chars)),
        )
        if args.write_manifest:
            manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
            _write_manifest(
                manifest_path,
                {
                    "generated_at_utc": _utc_now_iso(),
                    "mode": "single",
                    "results": [asdict(result)],
                },
            )

        if result.ok:
            print(f"OK: extracted text via {result.backend} -> {result.output_txt}")
            print(f"Chars: {result.chars_written}")
            return 0

        print(f"ERROR: {result.error}")
        return 2

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    if args.out:
        raise SystemExit("--out is only valid with --pdf")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (input_dir / "pdf_extract")
    results = extract_pdf_directory(
        input_dir,
        output_dir=output_dir,
        max_pages=args.max_pages,
        max_chars=max(1, int(args.max_chars)),
    )

    if args.write_manifest:
        _write_manifest(
            output_dir / "manifest.json",
            {
                "generated_at_utc": _utc_now_iso(),
                "mode": "batch",
                "input_dir": str(input_dir).replace("\\", "/"),
                "output_dir": str(output_dir).replace("\\", "/"),
                "max_pages": args.max_pages,
                "max_chars": max(1, int(args.max_chars)),
                "results": [asdict(r) for r in results],
            },
        )

    ok_count = sum(1 for r in results if r.ok)
    print(f"[extract] pdfs={len(results)} ok={ok_count} failed={len(results) - ok_count}")
    if len(results) == 0:
        print("[extract] no PDFs found")
    return 0 if all(r.ok for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())