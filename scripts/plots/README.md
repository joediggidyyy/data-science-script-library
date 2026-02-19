# plots

Quick visualization helpers intended for fast feedback loops in data science work.

## Included scripts

- `plot_timeseries_from_csv.py`
  - Create a simple line chart from a CSV file and write it to a PNG.
  - Defaults: first column is x-axis, numeric-looking columns are plotted as y series.
- `plot_score_distribution.py`
  - Plot distribution of anomaly scores from a `score_raw` column.
- `plot_threshold_impact.py`
  - Visualize threshold placement and flagged-region impact for `score_raw` values.

## Usage examples

Plot one series explicitly:

```text
python scripts/plots/plot_timeseries_from_csv.py input.csv --out out/plot.png --x timestamp --y value
```

Let the script infer numeric y columns:

```text
python scripts/plots/plot_timeseries_from_csv.py input.csv --out out/plot.png
```

Plot anomaly score distribution:

```text
python scripts/plots/plot_score_distribution.py scores.csv out/score_distribution.png
```

Plot threshold impact:

```text
python scripts/plots/plot_threshold_impact.py scores.csv 0.12 out/threshold_impact.png
```
