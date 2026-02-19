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
- Added data validation + evaluation utilities:
	- `scripts/data/validate_jsonl_records.py`
	- `scripts/ml/evaluate_scores_report.py`
- Added data engineering + ML pipeline utilities:
	- `scripts/data/build_feature_dataset.py`
	- `scripts/ml/train_sklearn_model.py`
	- `scripts/ml/score_unsupervised_model.py`
	- `scripts/ml/run_ml_pipeline_demo.py`
- Added repo/runtime audit utilities:
	- `scripts/repo/audit/audit_repo_health_snapshot.py`
	- `scripts/repo/audit/audit_runtime_artifacts_snapshot.py`
	- `scripts/repo/audit/audit_status_drift.py`
	- `scripts/repo/audit/report_runtime_parameters.py`
	- `scripts/repo/audit/audit_web_dashboard_endpoints.py`
	- `scripts/repo/audit/check_pidfiles_status.py`
- Added/updated tests and README index coverage for expanded script surface.
- Added one-command maintenance workflow:
	- `maintain.py`
	- `MAINTENANCE.md`
	- `MAINTENANCE_JOB_2026-02-19.md`
- Added student setup automation + tutorial:
	- `scripts/repo/setup/setup_student_env.py`
	- `tutorials/VENV_AND_JUPYTER_VSCODE_TUTORIAL.md`
- Split onboarding tutorials by operating system:
	- `tutorials/VENV_JUPYTER_WINDOWS.md`
	- `tutorials/VENV_JUPYTER_MACOS.md`
	- `tutorials/VENV_JUPYTER_LINUX.md`
- Added first-week lab notebook onboarding assets:
	- `notebooks/first_week_lab_template.ipynb`
	- setup integration to create `notebooks/first_week_lab.ipynb` by default
- Added fast maintenance option:
	- `maintain.py --quick`
- Added pytest coverage for new onboarding/maintenance surfaces:
	- `tests/test_setup_student_env.py`
	- `tests/test_maintain_quick_mode.py`
	- `tests/test_first_week_lab_template.py`
- Added TensorFlow class setup profile support:
	- `scripts/repo/setup/setup_student_env.py --deps tensorflow-class --python <python3.13>`
	- Enforced Python 3.13 check for this profile
- Updated `SECURITY.md` with notebook/report hygiene, setup safety, names-only reporting, and dependency-profile guidance
- Synced all public README-flavor files with current setup/security references

