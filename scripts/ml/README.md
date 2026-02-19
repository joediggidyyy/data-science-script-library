# ML

Small ML utilities and educational reference implementations.

The emphasis is on clarity over cleverness: scripts here are short enough to read, reason about, and adapt for assignments.

## Included scripts

- `solver.py` — `ApexRegressor`: projected gradient descent regression with simplex constraints.
- `train_test_split_cli.py` — Deterministic train/test split for CSV datasets (optional stratification + indices export).
- `model_eval_report.py` — Evaluation metrics reports for classification/regression from `y_true` and `y_pred` CSVs.
- `select_anomaly_threshold.py` — Select anomaly threshold from score distributions for a target FPR.
- `evaluate_scores_report.py` — Evaluate score thresholds in labeled/unlabeled mode and write JSON + Markdown artifacts.
- `train_sklearn_model.py` — Train supervised (Random Forest) or unsupervised (Isolation Forest) models from dataset manifests.
- `score_unsupervised_model.py` — Score dataset records with unsupervised models and write `record_id,score_raw` CSV.
- `run_ml_pipeline_demo.py` — Execute a synthetic end-to-end pipeline demo (dataset build, train, score).

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

Select threshold for anomaly scores:

```text
python scripts/ml/select_anomaly_threshold.py --scores scores.csv --target-fpr 0.01 --out-report out/threshold_report.md
```

Evaluate score thresholds with labels (FPR-constrained):

```text
python scripts/ml/evaluate_scores_report.py --scores-csv scores.csv --labels-csv labels.csv --id-col record_id --label-col label --positive-label 1 --max-fpr 0.01 --out-dir out/
```

Train an unsupervised model from a dataset manifest:

```text
python scripts/ml/train_sklearn_model.py --dataset out/dataset/dataset_manifest.json --out-dir out/model --model-type unsupervised
```

Score records with the trained model:

```text
python scripts/ml/score_unsupervised_model.py --dataset out/dataset/dataset_manifest.json --model out/model/train_manifest.json --out-file out/scores/scores.csv
```

## Related docs

- Setup/tutorial hub: `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
- TensorFlow class profile (Python 3.13): `scripts/repo/setup/setup_student_env.py --deps tensorflow-class --python <python3.13>`
- Security guidance: `SECURITY.md`

