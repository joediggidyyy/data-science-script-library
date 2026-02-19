# Markdown

Markdown hygiene helpers.

These scripts detect common markdown issues that show up in student repos (commands written as plain text, formatting drift) and help keep docs copy/pasteable.

## Included scripts

- `check_command_blocks.py` — Flags command-like lines (e.g., `python`, `pip`, `git`) that appear outside fenced code blocks.

## Usage examples

Scan a single file:

```text
python scripts/docs/markdown/check_command_blocks.py README.md
```

Scan a directory recursively (default: `.md`):

```text
python scripts/docs/markdown/check_command_blocks.py docs
```

Add additional prefixes to flag (repeatable):

```text
python scripts/docs/markdown/check_command_blocks.py . --prefix conda --prefix uv
```

## Related docs

- Setup/tutorial hub: `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
- Security guidance: `SECURITY.md`

