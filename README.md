# Data Science Script Library

A small library of standalone scripts that are useful for students doing data science, analytics, and ML coursework.

> This Repository is Maintained _by CodeSentinel_

## Script Index

### Benchmarks
- [`benchmark_simulator.py`](scripts/benchmarks/benchmark_simulator.py) — Simple graph benchmarking simulator (expects a graph JSON file).

### Data
- [`jsonl_to_csv.py`](scripts/data/jsonl_to_csv.py) — Convert JSONL (one object per line) to CSV with inferred or explicit columns.
  - [`jsonl_profile.py`](scripts/data/jsonl_profile.py) — Profile JSONL (schema, field frequency, null counts, examples) -> JSON + Markdown.
  - [`csv_profile_report.py`](scripts/data/csv_profile_report.py) — Profile CSV (missing/uniques/numeric stats + samples) -> Markdown + HTML.
  - [`data_cleaning_recipes.py`](scripts/data/data_cleaning_recipes.py) — Conservative CSV cleanup recipes (normalize columns, trim whitespace, drop empties/dupes).
  - [`parquet_inspect.py`](scripts/data/parquet_inspect.py) — Inspect Parquet schema + basic metadata (requires `pyarrow`).
  - [`inspect_jsonl_gz_archive.py`](scripts/data/inspect_jsonl_gz_archive.py) — Inspect `.jsonl.gz` archives (record counts, key frequencies, sample records).
  - [`validate_jsonl_records.py`](scripts/data/validate_jsonl_records.py) — Validate JSONL records with configurable forbidden/allowed key policies.
  - [`build_feature_dataset.py`](scripts/data/build_feature_dataset.py) — Build feature datasets from JSONL into features/labels/splits + manifest artifacts.
  - Back-compat alias: [`metrics_exporter.py`](scripts/data/metrics_exporter.py) (deprecated)

### Docs
- [`convert_to_pdf.py`](scripts/docs/convert_to_pdf.py) — Convert Markdown to PDF (basic formatting).
- [`md_to_slides.py`](scripts/docs/md_to_slides.py) — Convert Markdown to a reveal.js HTML slide deck.
- [`check_command_blocks.py`](scripts/docs/markdown/check_command_blocks.py) — Flag plaintext command lines outside fenced code blocks.
- [`clean_unicode.py`](scripts/docs/text/clean_unicode.py) — Replace common unicode punctuation/symbols with ASCII-safe equivalents.

### ML
- [`solver.py`](scripts/ml/solver.py) — `ApexRegressor`: projected gradient descent regression with simplex constraints.
- [`train_test_split_cli.py`](scripts/ml/train_test_split_cli.py) — Deterministic train/test split for CSV (optional stratification).
- [`model_eval_report.py`](scripts/ml/model_eval_report.py) — Model evaluation report for classification/regression (JSON + Markdown).
- [`select_anomaly_threshold.py`](scripts/ml/select_anomaly_threshold.py) — Select anomaly threshold for a target false-positive rate from score distributions.
- [`evaluate_scores_report.py`](scripts/ml/evaluate_scores_report.py) — Evaluate score thresholds in labeled/unlabeled modes and emit JSON + Markdown reports.
- [`train_sklearn_model.py`](scripts/ml/train_sklearn_model.py) — Train supervised/unsupervised sklearn models from dataset manifests.
- [`score_unsupervised_model.py`](scripts/ml/score_unsupervised_model.py) — Score feature records with unsupervised models and emit `record_id,score_raw` CSV.
- [`run_ml_pipeline_demo.py`](scripts/ml/run_ml_pipeline_demo.py) — Run a synthetic end-to-end demo (build dataset -> train -> score).

### Notebooks
- [`export_notebook.py`](scripts/notebooks/export_notebook.py) — Export `.ipynb` to HTML/PDF (supports tag-based removal).
- [`notebook_scrub_secrets.py`](scripts/notebooks/notebook_scrub_secrets.py) — Redact common secret patterns + clear outputs for safer sharing.
- [`notebook_parameter_sweep.py`](scripts/notebooks/notebook_parameter_sweep.py) — Inject a `parameters` cell and run a notebook over a parameter grid.

### Plots
- [`plot_timeseries_from_csv.py`](scripts/plots/plot_timeseries_from_csv.py) — Quick time-series line charts from CSV -> PNG.
- [`plot_score_distribution.py`](scripts/plots/plot_score_distribution.py) — Plot score distributions (`score_raw`) with KDE and summary stats.
- [`plot_threshold_impact.py`](scripts/plots/plot_threshold_impact.py) — Visualize threshold impact and flagged rate over score distributions.

### Repo helpers

- Inventory:
  - [`generate_script_inventory.py`](scripts/repo/inventory/generate_script_inventory.py) — Generate JSON + Markdown script inventory for a directory.
  - [`inventory_json_to_csv.py`](scripts/repo/inventory/inventory_json_to_csv.py) — Convert inventory JSON to CSV.
- Analysis:
  - [`find_duplicate_functions.py`](scripts/repo/analysis/find_duplicate_functions.py) — Find exact duplicate function bodies.
  - [`find_near_duplicate_functions.py`](scripts/repo/analysis/find_near_duplicate_functions.py) — Find near-duplicate functions via AST-normalized similarity.
- Audit:
  - [`audit_vscode_crash_logs.py`](scripts/repo/audit/audit_vscode_crash_logs.py) — Collect VS Code crash/instability evidence from local logs.
  - [`triage_vscode_crash_remediation.py`](scripts/repo/audit/triage_vscode_crash_remediation.py) — Generate remediation triage from crash evidence (+ optional attribution).
  - [`audit_repo_health_snapshot.py`](scripts/repo/audit/audit_repo_health_snapshot.py) — Snapshot repository hygiene findings (tracked-path and ignore-policy checks).
  - [`audit_runtime_artifacts_snapshot.py`](scripts/repo/audit/audit_runtime_artifacts_snapshot.py) — Snapshot runtime heartbeat/telemetry/log artifact freshness.
  - [`audit_status_drift.py`](scripts/repo/audit/audit_status_drift.py) — Audit status drift between task SSOT, dashboards, and task documents.
  - [`report_runtime_parameters.py`](scripts/repo/audit/report_runtime_parameters.py) — Report runtime parameter surface (env names + path checks, names-only).
  - [`audit_web_dashboard_endpoints.py`](scripts/repo/audit/audit_web_dashboard_endpoints.py) — Audit web dashboard endpoints with names-only response evidence.
  - [`check_pidfiles_status.py`](scripts/repo/audit/check_pidfiles_status.py) — Check whether PID-file-referenced processes are running.

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
- Distribution plots: `pandas`, `seaborn`, `matplotlib` (`scripts/plots/plot_score_distribution.py`, `scripts/plots/plot_threshold_impact.py`)
- ML evaluation: `scikit-learn` (`scripts/ml/model_eval_report.py`)
- Parquet: `pyarrow` (`scripts/data/parquet_inspect.py`)
- PDF (web exporter): `nbconvert[webpdf]` (`scripts/notebooks/export_notebook.py`)

## Notes

- These scripts are intended to be copy-paste friendly.
- Outputs like `.html` and `.pdf` are ignored by default via `.gitignore`.

---

See also: `SECURITY.md` and `CONTRIBUTING.md`.
