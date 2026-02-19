# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Initial scaffolding

## 2026-02-19

- Added ML utility:
	- `scripts/ml/select_anomaly_threshold.py`
- Added plotting utilities:
	- `scripts/plots/plot_score_distribution.py`
	- `scripts/plots/plot_threshold_impact.py`
- Added data archive utility:
	- `scripts/data/inspect_jsonl_gz_archive.py`
- Added repo audit utilities:
	- `scripts/repo/audit/audit_vscode_crash_logs.py`
	- `scripts/repo/audit/triage_vscode_crash_remediation.py`
- Updated docs/indexes for all additions and expanded full dependency set (`pandas`, `seaborn`).

## 2026-02-20

- Added data validation utility:
	- `scripts/data/validate_jsonl_records.py`
- Added ML score evaluation utility:
	- `scripts/ml/evaluate_scores_report.py`
- Added repo/runtime audit utilities:
	- `scripts/repo/audit/audit_repo_health_snapshot.py`
	- `scripts/repo/audit/audit_runtime_artifacts_snapshot.py`
	- `scripts/repo/audit/audit_status_drift.py`
	- `scripts/repo/audit/report_runtime_parameters.py`
- Added tests for all Batch B scripts and updated script index documentation.

## 2026-02-21

- Added data engineering utility:
	- `scripts/data/build_feature_dataset.py`
- Added ML pipeline utilities:
	- `scripts/ml/train_sklearn_model.py`
	- `scripts/ml/score_unsupervised_model.py`
	- `scripts/ml/run_ml_pipeline_demo.py`
- Added repo/runtime audit helpers:
	- `scripts/repo/audit/audit_web_dashboard_endpoints.py`
	- `scripts/repo/audit/check_pidfiles_status.py`
- Added Batch C planning artifacts, tests, and README index updates.

