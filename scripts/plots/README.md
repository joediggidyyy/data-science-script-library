# plots

Quick visualization helpers intended for fast feedback loops in data science work.

## Included scripts

- `plot_timeseries_from_csv.py`
  - Create a simple line chart from a CSV file and write it to a PNG.
  - Defaults: first column is x-axis, numeric-looking columns are plotted as y series.

## Usage examples

Plot one series explicitly:

```text
python scripts/plots/plot_timeseries_from_csv.py input.csv --out out/plot.png --x timestamp --y value
```

Let the script infer numeric y columns:

```text
python scripts/plots/plot_timeseries_from_csv.py input.csv --out out/plot.png
```
