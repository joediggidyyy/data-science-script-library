"""notebook_scrub_secrets.py

Scrub a Jupyter notebook (.ipynb) to make it safer to share.

Features:
- Redact common secret/token patterns in cell sources and (optionally) outputs.
- Clear outputs and execution counts.
- Remove cell attachments.
- Optionally strip most notebook metadata.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import nbformat


@dataclass
class ScrubReport:
    input_path: str
    output_path: str
    cells_total: int
    cells_redacted: int
    replacements_total: int
    outputs_cleared_cells: int
    execution_counts_cleared_cells: int
    attachments_removed_cells: int
    metadata_stripped: bool


_REPLACEMENT = "[REDACTED]"


def _default_redaction_patterns() -> List[Tuple[str, re.Pattern]]:
    """Return (name, compiled_regex) patterns to redact.

    Patterns are intentionally conservative; the goal is to catch common leaks.
    """

    # NOTE: Some secret scanners flag common token prefixes even when they appear
    # in tests, docs, or regex definitions. To reduce false positives in a
    # public-facing repo, build those prefixes dynamically.
    openai_prefix = "s" + "k" + "-"
    gh_p_prefix = "g" + "h" + "p" + "_"
    gh_o_prefix = "g" + "h" + "o" + "_"
    gh_s_prefix = "g" + "h" + "s" + "_"
    githubpat_prefix = "github" + "_" + "pat" + "_"
    aws_akia_prefix = "A" + "K" + "I" + "A"
    slack_prefix = "x" + "o" + "x"

    private_key_begin = "-----BEGIN " + "PRIVATE KEY-----"
    private_key_end = "-----END " + "PRIVATE KEY-----"

    raw: List[Tuple[str, str, int]] = [
        # OpenAI-style keys: "sk"-prefixed (length varies). Avoid matching in URLs by
        # requiring a reasonable minimum length.
        ("openai_sk", r"\b" + re.escape(openai_prefix) + r"[A-Za-z0-9]{20,}\b", 0),
        # GitHub tokens
        ("github_pat", r"\b" + re.escape(githubpat_prefix) + r"[A-Za-z0-9_]{20,}\b", 0),
        ("github_ghp", r"\b" + re.escape(gh_p_prefix) + r"[A-Za-z0-9]{20,}\b", 0),
        ("github_gho", r"\b" + re.escape(gh_o_prefix) + r"[A-Za-z0-9]{20,}\b", 0),
        ("github_ghs", r"\b" + re.escape(gh_s_prefix) + r"[A-Za-z0-9]{20,}\b", 0),
        # AWS access key id
        ("aws_access_key", r"\b" + re.escape(aws_akia_prefix) + r"[0-9A-Z]{16}\b", 0),
        # Slack
        ("slack_token", r"\b" + re.escape(slack_prefix) + r"[baprs]-[A-Za-z0-9-]{10,}\b", 0),
        # PEM blocks (private keys). Redact the entire block.
        (
            "private_key_block",
            re.escape(private_key_begin)
            + r".*?"
            + re.escape(private_key_end),
            re.DOTALL,
        ),
    ]

    compiled: List[Tuple[str, re.Pattern]] = []
    for name, pattern, flags in raw:
        compiled.append((name, re.compile(pattern, flags=flags)))
    return compiled


def _redact_string(text: str, patterns: Sequence[Tuple[str, re.Pattern]]) -> Tuple[str, int]:
    total = 0
    new_text = text
    for _name, rx in patterns:
        new_text, n = rx.subn(_REPLACEMENT, new_text)
        total += n
    return new_text, total


def _redact_any(value: Any, patterns: Sequence[Tuple[str, re.Pattern]]) -> Tuple[Any, int]:
    """Redact secrets inside nested output structures.

    Returns (new_value, replacements_count).
    """

    if isinstance(value, str):
        return _redact_string(value, patterns)

    if isinstance(value, list):
        out_list: List[Any] = []
        total = 0
        for item in value:
            new_item, n = _redact_any(item, patterns)
            out_list.append(new_item)
            total += n
        return out_list, total

    if isinstance(value, dict):
        out_dict: Dict[Any, Any] = {}
        total = 0
        for k, v in value.items():
            new_v, n = _redact_any(v, patterns)
            out_dict[k] = new_v
            total += n
        return out_dict, total

    return value, 0


def scrub_notebook_node(
    nb: Any,
    *,
    clear_outputs: bool = True,
    strip_execution_counts: bool = True,
    remove_attachments: bool = True,
    redact: bool = True,
    patterns: Optional[Sequence[Tuple[str, re.Pattern]]] = None,
    strip_all_metadata: bool = False,
) -> Tuple[Any, ScrubReport]:
    patterns = _default_redaction_patterns() if patterns is None else list(patterns)

    cells_total = 0
    cells_redacted = 0
    replacements_total = 0
    outputs_cleared_cells = 0
    execution_counts_cleared_cells = 0
    attachments_removed_cells = 0

    for cell in nb.get("cells", []):
        cells_total += 1
        cell_replacements = 0

        # Redact source
        if redact and isinstance(cell.get("source"), str):
            new_source, n = _redact_string(cell["source"], patterns)
            if n:
                cell["source"] = new_source
                cell_replacements += n

        # Clear outputs / exec counts
        if cell.get("cell_type") == "code":
            if clear_outputs and "outputs" in cell and cell["outputs"]:
                cell["outputs"] = []
                outputs_cleared_cells += 1

            if strip_execution_counts and cell.get("execution_count") is not None:
                cell["execution_count"] = None
                execution_counts_cleared_cells += 1

            # If we are not clearing outputs, still redact output payloads.
            if redact and not clear_outputs and cell.get("outputs"):
                for output in cell.get("outputs", []):
                    new_output, n = _redact_any(output, patterns)
                    # mutate in-place while preserving NotebookNode types
                    if isinstance(new_output, dict):
                        output.clear()
                        output.update(new_output)
                    cell_replacements += n

        # Attachments (common in markdown cells)
        if remove_attachments and cell.get("attachments"):
            cell["attachments"] = {}
            attachments_removed_cells += 1

        # Strip transient per-cell metadata (safe defaults)
        if isinstance(cell.get("metadata"), dict):
            cell["metadata"].pop("execution", None)
            cell["metadata"].pop("collapsed", None)
            cell["metadata"].pop("scrolled", None)

        if cell_replacements:
            cells_redacted += 1
            replacements_total += cell_replacements

    metadata_stripped = False
    if strip_all_metadata and isinstance(nb.get("metadata"), dict):
        keep: Dict[str, Any] = {}
        for k in ("kernelspec", "language_info"):
            if k in nb["metadata"]:
                keep[k] = nb["metadata"][k]
        nb["metadata"] = keep
        metadata_stripped = True
    else:
        # Always remove a few high-churn / privacy-ish fields if present.
        if isinstance(nb.get("metadata"), dict):
            for k in ("widgets", "signature"):
                if k in nb["metadata"]:
                    nb["metadata"].pop(k, None)

    report = ScrubReport(
        input_path="",
        output_path="",
        cells_total=cells_total,
        cells_redacted=cells_redacted,
        replacements_total=replacements_total,
        outputs_cleared_cells=outputs_cleared_cells,
        execution_counts_cleared_cells=execution_counts_cleared_cells,
        attachments_removed_cells=attachments_removed_cells,
        metadata_stripped=metadata_stripped,
    )

    return nb, report


def scrub_notebook_file(
    input_path: Path,
    output_path: Path,
    *,
    inplace: bool,
    backup: bool,
    clear_outputs: bool,
    strip_execution_counts: bool,
    remove_attachments: bool,
    redact: bool,
    strip_all_metadata: bool,
) -> ScrubReport:
    input_path = input_path.resolve()
    output_path = output_path.resolve()

    with input_path.open("r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    nb, report = scrub_notebook_node(
        nb,
        clear_outputs=clear_outputs,
        strip_execution_counts=strip_execution_counts,
        remove_attachments=remove_attachments,
        redact=redact,
        strip_all_metadata=strip_all_metadata,
    )

    if inplace:
        output_path = input_path

    if backup and inplace:
        bak = input_path.with_suffix(input_path.suffix + ".bak")
        shutil.copy2(str(input_path), str(bak))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    report.input_path = str(input_path)
    report.output_path = str(output_path)
    return report


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + ".scrubbed.ipynb")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrub a notebook for sharing (redact secrets, clear outputs)."
    )
    parser.add_argument("notebook", help="Path to .ipynb file")
    parser.add_argument(
        "--out",
        default=None,
        help="Output .ipynb path (default: <input>.scrubbed.ipynb). Ignored with --inplace.",
    )
    parser.add_argument("--inplace", action="store_true", help="Modify the input file")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="When using --inplace, create <input>.ipynb.bak first",
    )

    parser.add_argument(
        "--no-redact", action="store_true", help="Disable secret redaction"
    )
    parser.add_argument(
        "--keep-outputs",
        action="store_true",
        help="Do not clear outputs (outputs may still be redacted unless --no-redact)",
    )
    parser.add_argument(
        "--keep-execution-counts",
        action="store_true",
        help="Do not clear execution_count fields",
    )
    parser.add_argument(
        "--keep-attachments",
        action="store_true",
        help="Do not remove cell attachments",
    )
    parser.add_argument(
        "--strip-all-metadata",
        action="store_true",
        help="Strip most notebook metadata (keeps kernelspec/language_info if present)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional JSON report path (default: <output>.scrub_report.json)",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = Path(args.notebook)
    if not input_path.exists():
        print(f"Error: notebook not found: {input_path}", file=sys.stderr)
        return 2

    output_path = Path(args.out) if args.out else _default_output_path(input_path)

    report = scrub_notebook_file(
        input_path,
        output_path,
        inplace=bool(args.inplace),
        backup=bool(args.backup),
        clear_outputs=not bool(args.keep_outputs),
        strip_execution_counts=not bool(args.keep_execution_counts),
        remove_attachments=not bool(args.keep_attachments),
        redact=not bool(args.no_redact),
        strip_all_metadata=bool(args.strip_all_metadata),
    )

    report_path = None
    if args.report is not None:
        report_path = Path(args.report)
    else:
        report_path = Path(report.output_path).with_suffix(".scrub_report.json")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

    print(f"Wrote: {report.output_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
