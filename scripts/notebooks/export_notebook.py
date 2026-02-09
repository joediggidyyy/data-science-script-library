"""export_notebook.py

Export a Jupyter notebook (.ipynb) to HTML or PDF.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

import argparse
from pathlib import Path
import sys
from typing import Optional

def export_notebook(notebook_path: str, output_format: str = 'html', output_path: Optional[str] = None) -> int:
    """Export a Jupyter notebook to HTML or PDF.

    This script keeps notebook dependencies optional by importing them lazily.
    """

    notebook_path_obj = Path(notebook_path).expanduser().resolve()
    if not notebook_path_obj.exists():
        print(f"Error: File not found: {notebook_path_obj}", file=sys.stderr)
        return 2

    # Lazy imports for optional dependencies.
    try:
        import nbformat  # type: ignore
        from traitlets.config import Config  # type: ignore
        from nbconvert import HTMLExporter, PDFExporter  # type: ignore
        from nbconvert.exporters import WebPDFExporter  # type: ignore
        from nbconvert.preprocessors import TagRemovePreprocessor  # type: ignore
    except Exception as exc:
        print(
            "Notebook export requires optional dependencies. Install 'nbconvert', 'nbformat', and 'traitlets' and retry. "
            f"(import error: {exc})",
            file=sys.stderr,
        )
        return 2

    print(f"Reading: {notebook_path_obj.name}")
    try:
        nb = nbformat.read(str(notebook_path_obj), as_version=4)
    except Exception as exc:
        print(f"Error: Failed to read notebook: {exc}", file=sys.stderr)
        return 2

    exporter = None
    output_ext = ''

    if output_format == 'html':
        exporter = HTMLExporter()
        output_ext = '.html'
    elif output_format == 'pdf':
        # Check for webpdf dependencies (pyppeteer) or latex
        try:
            # Prefer WebPDF (Headless Chrome) over LaTeX for ease of setup
            exporter = WebPDFExporter() 
            output_ext = '.pdf'
        except Exception as e:
            print(f"WebPDF exporter not available: {e}")
            print("Falling back to standard PDF (Requires LaTeX/Pandoc)...")
            exporter = PDFExporter()
            output_ext = '.pdf'
    
    if not exporter:
        print("Could not initialize exporter.", file=sys.stderr)
        return 2

    # Configure
    c = Config()
    c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell",)
    c.TagRemovePreprocessor.remove_input_tags = ("remove_input",)
    c.TagRemovePreprocessor.enabled = True
    exporter.register_preprocessor(TagRemovePreprocessor(config=c), enabled=True)

    try:
        print(f"Converting to {output_format.upper()}...")
        (body, resources) = exporter.from_notebook_node(nb)

        output_path_obj = Path(output_path).expanduser().resolve() if output_path else notebook_path_obj.with_suffix(output_ext)
        print(f"Writing: {output_path_obj}")

        if output_format == 'pdf':
            data = body.encode('utf-8', errors='replace') if isinstance(body, str) else bytes(body)
            output_path_obj.write_bytes(data)
        else:
            text = body.decode('utf-8', errors='replace') if isinstance(body, (bytes, bytearray)) else str(body)
            output_path_obj.write_text(text, encoding='utf-8')
            
        print("Success!")
        return 0
    except Exception as e:
        print(f"Export failed: {e}", file=sys.stderr)
        if output_format == 'pdf':
            print("\nTip: PDF export requires either:")
            print("1. 'pip install nbconvert[webpdf]' (plus Chromium)")
            print("2. Pandoc and MiKTeX installed on your system.")
            print("Ref: https://nbconvert.readthedocs.io/en/latest/install.html#installing-tex")
        return 2

def main():
    parser = argparse.ArgumentParser(description="Export Notebooks script")
    parser.add_argument("file", help="Path to .ipynb file")
    parser.add_argument("--format", choices=['html', 'pdf'], default='html', help="Output format")
    parser.add_argument("--output", default='', help="Optional output path")
    
    args = parser.parse_args()
    rc = export_notebook(args.file, args.format, args.output or None)
    raise SystemExit(rc)

if __name__ == "__main__":
    main()
