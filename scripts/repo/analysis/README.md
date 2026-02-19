# Analysis

Repository code analysis helpers for identifying duplicated code and refactoring candidates.

## Included scripts

- `find_duplicate_functions.py` — AST-based exact duplicate function detection across Python files.
- `find_near_duplicate_functions.py` — AST-normalized fuzzy near-duplicate detection.

## Usage examples

Exact duplicates (fast, strict):

```text
python scripts/repo/analysis/find_duplicate_functions.py --root . --out report_tmp/dupes
```

Near duplicates (slower, similarity-based):

```text
python scripts/repo/analysis/find_near_duplicate_functions.py --root . --out report_tmp/near_dupes --threshold 0.9
```

## Related docs

- Setup/tutorial hub: `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
- Security guidance: `SECURITY.md`

