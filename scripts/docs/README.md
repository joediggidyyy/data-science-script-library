# Docs

Documentation utilities for validating, converting, and publishing Markdown.

## Included scripts

- `convert_to_pdf.py` — Convert Markdown (`.md`) to PDF using ReportLab.
- `md_to_slides.py` — Convert Markdown to a reveal.js HTML slide deck (slides split on `---`).

## Subdirectories

- `markdown/` — Markdown hygiene checks (style, command fencing)
- `text/` — Text transforms (unicode cleanup)

## Usage examples

Convert Markdown to PDF:

```text
python scripts/docs/convert_to_pdf.py README.md README.pdf
```

Convert Markdown to reveal.js slides:

```text
python scripts/docs/md_to_slides.py talk.md talk.html
```

Scan a docs folder and flag plaintext command lines outside fenced code blocks:

```text
python scripts/docs/markdown/check_command_blocks.py docs --ext .md
```

Normalize unicode punctuation in-place (writes backups):

```text
python scripts/docs/text/clean_unicode.py . --ext .md --inplace --backup-suffix .bak
```

