# Security Policy

## Reporting

If you discover a security issue, please report it privately.

- Do not open a public issue for vulnerabilities.

## Secrets

- Do not commit API keys, passwords, tokens, or credentials.
- Use environment variables for sensitive configuration.

## Notebook and report hygiene

- Treat notebooks as publishable artifacts: scrub outputs and sensitive strings before sharing.
- Use `scripts/notebooks/notebook_scrub_secrets.py` for notebook redaction workflows.
- Prefer names-only reporting for operational diagnostics (`scripts/repo/audit/*`).

## Environment safety

- Use per-project virtual environments only (never global installs for class projects).
- Use the setup automation script for consistent bootstrap:
	- `scripts/repo/setup/setup_student_env.py`
- Default setup is non-interactive; `--interactive` is available for guided onboarding.

## Python and dependency profiles

- Core profile (`--deps core`) is the default and lowest-risk baseline.
- Full profile (`--deps full`) includes optional plotting/ML/parquet extras.
- TensorFlow-class profile (`--deps tensorflow-class`) requires **Python 3.13** and enforces this check at setup time.

## Supply chain

- Install from repository requirements files (`requirements*.txt`) rather than ad-hoc package lists.
- Keep dependency footprint minimal for student projects unless course requirements explicitly need additional libraries.
- Pin or constrain versions when practical.

---

For the overarching CodeSentinel security posture, see the main project `SECURITY.md`.

> This Repository is Maintained _by CodeSentinel_
