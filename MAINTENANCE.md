# Maintenance

This repository has two aligned purposes:

1. **Student utility** — practical, copy/paste-friendly data-science scripts.
2. **Professional exhibition** — a clean example of CodeSentinel operational discipline.

To keep both goals healthy, use the single maintenance entrypoint from this repository root:

```text
python maintain.py
```

Fast maintenance path:

```text
python maintain.py --quick
```

## What `maintain.py` does

- inventories script and test surfaces
- checks changelog date integrity (future-dated release headers)
- runs the local test suite (`pytest tests`)
- runs duplicate-function analysis
- refreshes `CODE_QUALITY_AUDIT_REPORT.md`
- maintains a sub-repo baseline hash artifact at `maintenance/script_library_baseline.json`
- writes run evidence to `report_tmp/maintenance/`

## Optional flags

```text
python maintain.py --quick
python maintain.py --dry-run
python maintain.py --strict
python maintain.py --refresh-baseline
```

Notes:

- `--quick` skips pytest and duplicate-function scan for a fast status pass.
- `--strict` treats warnings (for example, future-dated changelog headers) as failures.
- Baseline refresh is explicit after bootstrap (`--refresh-baseline`) to avoid accidental drift churn.

## Student environment setup

- Automated setup script: `scripts/repo/setup/setup_student_env.py`
	- default: non-interactive
	- guided prompts: `--interactive`
- Full tutorial: `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
