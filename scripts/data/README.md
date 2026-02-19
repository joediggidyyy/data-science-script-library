# data

Small, dependency-free utilities for “data plumbing” tasks: converting logs and records into CSV for spreadsheets, plotting, or quick inspection.

## Included scripts

- `jsonl_to_csv.py`
  - Converts JSONL (one JSON object per line) to CSV.
  - Field order is inferred (stable first-seen order) unless you provide `--fields`.
- `jsonl_profile.py`
  - Profiles a JSONL file and emits JSON + Markdown reports (field frequency, null counts, observed types, example values).
- `csv_profile_report.py`
  - Profiles a CSV and emits Markdown + HTML reports (missing values, uniques, numeric stats, sample rows).
- `data_cleaning_recipes.py`
  - Apply small, conservative cleanup steps to a CSV (normalize columns, trim whitespace, drop empties/dupes).
- `parquet_inspect.py`
  - Inspect Parquet schema + basic metadata (requires `pyarrow`).
- `inspect_jsonl_gz_archive.py`
  - Inspect `.jsonl.gz` archives (record counts, key frequencies, sample records).
- `validate_jsonl_records.py`
  - Validate JSONL records with configurable forbidden/allowed key policies and optional strict unknown-key handling.
- `build_feature_dataset.py`
  - Build feature datasets from JSONL into `features.csv`, `labels.csv` (optional), `splits.csv`, and `dataset_manifest.json`.
- `metrics_exporter.py` (deprecated)
  - Backwards-compatible alias that enforces the historical stable column ordering used by some older CodeSentinel metrics logs.

## Usage examples

Infer columns from the file:

```text
python scripts/data/jsonl_to_csv.py input.jsonl output.csv
```

Enforce an explicit, stable schema:

```text
python scripts/data/jsonl_to_csv.py input.jsonl output.csv --fields timestamp,event,latency_ms
```

Use the deprecated alias (kept for older docs/scripts):

```text
python scripts/data/metrics_exporter.py metrics.jsonl metrics.csv
```

Profile a JSONL file (writes `jsonl_profile.json` and `jsonl_profile.md`):

```text
python scripts/data/jsonl_profile.py input.jsonl --out out/
```

Profile a CSV file (writes `csv_profile.md` and `csv_profile.html`):

```text
python scripts/data/csv_profile_report.py input.csv --out out/
```

Clean a CSV (writes `out.clean.csv` plus a JSON report):

```text
python scripts/data/data_cleaning_recipes.py input.csv --out out.clean.csv --normalize-columns --trim-whitespace --drop-empty-rows --drop-duplicate-rows
```

Inspect a Parquet file (human-readable):

```text
python scripts/data/parquet_inspect.py data.parquet
```

Inspect a gzipped JSONL archive:

```text
python scripts/data/inspect_jsonl_gz_archive.py data.jsonl.gz --top 30 --sample 1
```

Validate JSONL records with strict unknown-key policy:

```text
python scripts/data/validate_jsonl_records.py --input data.jsonl --allowed-keys record_id,score,label --strict-unknown-keys --json
```

Build a feature dataset from telemetry-like JSONL:

```text
python scripts/data/build_feature_dataset.py --input data.jsonl --out-dir out/dataset --seed 1337
```

## Related docs

- Setup/tutorial hub: `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
- Security guidance: `SECURITY.md`
