# ML

Small ML utilities and educational reference implementations.

The emphasis is on clarity over cleverness: scripts here are short enough to read, reason about, and adapt for assignments.

## Included scripts

- `solver.py` — `ApexRegressor`: projected gradient descent regression with simplex constraints.
- `train_test_split_cli.py` — Deterministic train/test split for CSV datasets (optional stratification + indices export).
- `model_eval_report.py` — Evaluation metrics reports for classification/regression from `y_true` and `y_pred` CSVs.

## Usage examples

Import and fit the constrained regressor:

```python
import numpy as np

from solver import ApexRegressor

X = np.array(
  [
    [1.0, 0.0, 0.5],
    [0.5, 1.0, 0.0],
    [1.0, 1.0, 1.0],
  ]
)
y = np.array([1.2, 0.7, 1.9])

model = ApexRegressor(learning_rate=0.05, max_iter=2000, tol=1e-8)
model.fit(X, y)
print(model.weights)  # non-negative and sums to ~1.0
```

Split a CSV into train/test deterministically (optionally stratified):

```text
python scripts/ml/train_test_split_cli.py dataset.csv --out out/ --test-size 0.2 --seed 1337 --stratify-col label --write-indices --preserve-order
```

Evaluate classification predictions and write JSON + Markdown reports:

```text
python scripts/ml/model_eval_report.py --task classification --y-true y_true.csv --y-pred y_pred.csv --out out/
```

Evaluate regression predictions:

```text
python scripts/ml/model_eval_report.py --task regression --y-true y_true.csv --y-pred y_pred.csv --out out/
```

