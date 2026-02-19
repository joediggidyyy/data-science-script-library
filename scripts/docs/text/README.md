# Text

Plain-text helpers for cleaning up text files in bulk.

These reduce cross-platform friction by normalizing characters that commonly break terminals, diffs, and CI (smart quotes, arrows, ellipsis, etc.).

## Included scripts

- `clean_unicode.py` — Replaces common unicode punctuation/symbols with ASCII-safe equivalents.

## Usage examples

Dry run (prints what would change; does not write files):

```text
python scripts/docs/text/clean_unicode.py . --ext .md
```

Modify files in place (writes backups):

```text
python scripts/docs/text/clean_unicode.py . --ext .md --inplace --backup-suffix .bak
```

## Related docs

- Setup/tutorial hub: `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
- Security guidance: `SECURITY.md`

