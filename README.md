# Data Science Script Library

A small library of standalone scripts that are useful for students doing data science, analytics, and ML coursework.

> This Repository is Maintained _by CodeSentinel_

## Script Index

### Benchmarks
- [`scripts/benchmarks/benchmark_simulator.py`](scripts/benchmarks/benchmark_simulator.py) — Simple graph benchmarking simulator (expects a graph JSON file).

### Data
- [`scripts/data/jsonl_to_csv.py`](scripts/data/jsonl_to_csv.py) — Convert JSONL (one object per line) to CSV with inferred or explicit columns.
  - [`scripts/data/jsonl_profile.py`](scripts/data/jsonl_profile.py) — Profile JSONL (schema, field frequency, null counts, examples) -> JSON + Markdown.
  - [`scripts/data/csv_profile_report.py`](scripts/data/csv_profile_report.py) — Profile CSV (missing/uniques/numeric stats + samples) -> Markdown + HTML.
  - [`scripts/data/data_cleaning_recipes.py`](scripts/data/data_cleaning_recipes.py) — Conservative CSV cleanup recipes (normalize columns, trim whitespace, drop empties/dupes).
  - [`scripts/data/parquet_inspect.py`](scripts/data/parquet_inspect.py) — Inspect Parquet schema + basic metadata (requires `pyarrow`).
  - Back-compat alias: [`scripts/data/metrics_exporter.py`](scripts/data/metrics_exporter.py) (deprecated)

### Docs
- [`scripts/docs/convert_to_pdf.py`](scripts/docs/convert_to_pdf.py) — Convert Markdown to PDF (basic formatting).
- [`scripts/docs/md_to_slides.py`](scripts/docs/md_to_slides.py) — Convert Markdown to a reveal.js HTML slide deck.
- [`scripts/docs/markdown/check_command_blocks.py`](scripts/docs/markdown/check_command_blocks.py) — Flag plaintext command lines outside fenced code blocks.
- [`scripts/docs/text/clean_unicode.py`](scripts/docs/text/clean_unicode.py) — Replace common unicode punctuation/symbols with ASCII-safe equivalents.

### ML
- [`scripts/ml/solver.py`](scripts/ml/solver.py) — `ApexRegressor`: projected gradient descent regression with simplex constraints.
- [`scripts/ml/train_test_split_cli.py`](scripts/ml/train_test_split_cli.py) — Deterministic train/test split for CSV (optional stratification).
- [`scripts/ml/model_eval_report.py`](scripts/ml/model_eval_report.py) — Model evaluation report for classification/regression (JSON + Markdown).

### Notebooks
- [`scripts/notebooks/export_notebook.py`](scripts/notebooks/export_notebook.py) — Export `.ipynb` to HTML/PDF (supports tag-based removal).
- [`scripts/notebooks/notebook_scrub_secrets.py`](scripts/notebooks/notebook_scrub_secrets.py) — Redact common secret patterns + clear outputs for safer sharing.
- [`scripts/notebooks/notebook_parameter_sweep.py`](scripts/notebooks/notebook_parameter_sweep.py) — Inject a `parameters` cell and run a notebook over a parameter grid.

### Plots
- [`scripts/plots/plot_timeseries_from_csv.py`](scripts/plots/plot_timeseries_from_csv.py) — Quick time-series line charts from CSV -> PNG.

### Repo helpers

- Inventory:
  - [`scripts/repo/inventory/generate_script_inventory.py`](scripts/repo/inventory/generate_script_inventory.py) — Generate JSON + Markdown script inventory for a directory.
  - [`scripts/repo/inventory/inventory_json_to_csv.py`](scripts/repo/inventory/inventory_json_to_csv.py) — Convert inventory JSON to CSV.
- Analysis:
  - [`scripts/repo/analysis/find_duplicate_functions.py`](scripts/repo/analysis/find_duplicate_functions.py) — Find exact duplicate function bodies.
  - [`scripts/repo/analysis/find_near_duplicate_functions.py`](scripts/repo/analysis/find_near_duplicate_functions.py) — Find near-duplicate functions via AST-normalized similarity.

## Quick start

1) Create and activate a virtual environment
2) Install dependencies:

- Core (lightweight):
  - `pip install -r requirements.txt`
- Full (includes optional heavier deps like matplotlib / scikit-learn / pyarrow):
  - `pip install -r requirements-full.txt`

## Dependencies

This library is split into:

- **Core deps** (declared in `requirements.txt` / `requirements-core.txt`): notebook handling and basic report generation.
- **Optional deps** (declared in `requirements-full.txt` and as extras in `pyproject.toml`): plotting, ML evaluation, Parquet inspection, and Markdown-to-slides.

Optional dependency map (by feature):

- Slides: `markdown2` (`scripts/docs/md_to_slides.py`)
- Plots: `matplotlib` (`scripts/plots/plot_timeseries_from_csv.py`)
- ML evaluation: `scikit-learn` (`scripts/ml/model_eval_report.py`)
- Parquet: `pyarrow` (`scripts/data/parquet_inspect.py`)
- PDF (web exporter): `nbconvert[webpdf]` (`scripts/notebooks/export_notebook.py`)

## Notes

- These scripts are intended to be copy-paste friendly.
- Outputs like `.html` and `.pdf` are ignored by default via `.gitignore`.

---

See also: `SECURITY.md` and `CONTRIBUTING.md`.
