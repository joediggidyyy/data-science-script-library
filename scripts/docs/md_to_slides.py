"""md_to_slides.py

Convert Markdown to a reveal.js HTML slide deck.

By default, slides are separated by a line containing only `---`.

This script intentionally uses CDN reveal.js assets for simplicity.
If you need offline decks, pass --reveal-base to point at local assets.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence


_HTML_TEMPLATE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"{reveal_base}/dist/reveal.css\" />
  <link rel=\"stylesheet\" href=\"{reveal_base}/dist/theme/{theme}.css\" id=\"theme\" />
  <style>
    .reveal pre code {{ max-height: 70vh; }}
    .reveal section img {{ max-height: 70vh; }}
  </style>
</head>
<body>
  <div class=\"reveal\">
    <div class=\"slides\">
{sections}
    </div>
  </div>

  <script src=\"{reveal_base}/dist/reveal.js\"></script>
  <script>
    Reveal.initialize({{
      hash: true,
      slideNumber: true,
    }});
  </script>
</body>
</html>
"""


def split_markdown_into_slides(markdown_text: str) -> List[str]:
    slides: List[str] = []
    current: List[str] = []

    for line in markdown_text.splitlines():
        if line.strip() == "---":
            slides.append("\n".join(current).strip())
            current = []
            continue
        current.append(line)

    slides.append("\n".join(current).strip())
    # Drop empty slides
    return [s for s in slides if s.strip()]


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown2  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Missing dependency: markdown2. Install it to use md_to_slides.py"
        ) from e

    # Enable fenced code blocks + tables (common for slide decks)
    return markdown2.markdown(markdown_text, extras=["fenced-code-blocks", "tables"])


def md_to_reveal_html(
    markdown_text: str,
    *,
    title: str,
    reveal_base: str,
    theme: str,
) -> str:
    slides = split_markdown_into_slides(markdown_text)
    sections = []
    for slide_md in slides:
        slide_html = markdown_to_html(slide_md)
        sections.append(f"      <section>\n{slide_html}\n      </section>")

    return _HTML_TEMPLATE.format(
        title=title,
        reveal_base=reveal_base.rstrip("/"),
        theme=theme,
        sections="\n".join(sections),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown to reveal.js slides")
    parser.add_argument("input", help="Input Markdown file")
    parser.add_argument("output", help="Output HTML file")
    parser.add_argument("--title", default=None, help="Deck title (default: input filename)")
    parser.add_argument(
        "--reveal-base",
        default="https://cdn.jsdelivr.net/npm/reveal.js@5",
        help="Base URL/path where reveal.js dist/ assets live",
    )
    parser.add_argument(
        "--theme",
        default="black",
        help="Reveal.js theme name (e.g., black, white, league, serif, simple, sky, solarized)",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Error: input not found: {in_path}", file=sys.stderr)
        return 2

    md = in_path.read_text(encoding="utf-8")
    title = args.title or in_path.stem

    try:
        html = md_to_reveal_html(
            md, title=title, reveal_base=str(args.reveal_base), theme=str(args.theme)
        )
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
