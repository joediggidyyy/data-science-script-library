# Notebooks

Notebook-focused utilities for common “submit-ready notebook” workflows.

Use these scripts to export notebooks for sharing, scrub secrets/outputs, and run lightweight parameter sweeps.

## Included scripts

- `export_notebook.py`
  - Export a notebook to HTML or PDF.
  - Supports tag-based removal:
    - `remove_cell` (remove entire cells)
    - `remove_input` (remove input areas)
- `notebook_scrub_secrets.py`
  - Scrub a notebook for sharing:
    - redact common secret/token patterns
    - clear outputs + execution counts
    - remove attachments
    - optionally strip most metadata
- `notebook_parameter_sweep.py`
  - Run a notebook across a parameter grid by injecting a cell tagged `parameters`.
  - Can either just write parameterized notebooks (`--no-execute`) or execute them.

## Usage examples

Export to HTML:

```text
python scripts/notebooks/export_notebook.py analysis.ipynb --format html
```

Export to PDF:

```text
python scripts/notebooks/export_notebook.py analysis.ipynb --format pdf
```

Scrub (write a new scrubbed notebook + JSON report):

```text
python scripts/notebooks/notebook_scrub_secrets.py analysis.ipynb
```

Scrub in-place (with backup):

```text
python scripts/notebooks/notebook_scrub_secrets.py analysis.ipynb --inplace --backup
```

Parameter sweep from a JSON grid (write parameterized notebooks only):

```text
python scripts/notebooks/notebook_parameter_sweep.py analysis.ipynb --grid grid.json --no-execute
```

Single run from CLI parameters (and execute):

```text
python scripts/notebooks/notebook_parameter_sweep.py analysis.ipynb --params x=3 --params name=\"demo\"
```

Tag behavior (set these tags in the notebook UI):

- `remove_cell`: remove the entire cell
- `remove_input`: keep outputs but hide the input/code area

## Notes

- PDF export can require additional system dependencies depending on the exporter backend.

