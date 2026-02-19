# Tests

These tests validate the standalone scripts under `scripts/`.

## Running tests

From the *CodeSentinel-1 repo root*, run:

```text
pytest projects/data-science-script-library/tests
```

## Notes

- The main CodeSentinel test suite is configured (via the repo root `pytest.ini`) to run `tests/` by default.
- These tests live alongside the repo snapshot so they can be copied out cleanly when you publish/extract `projects/data-science-script-library/` into its own repository.
- Setup automation under test: `scripts/repo/setup/setup_student_env.py` (including Python 3.13 tensorflow-class gating).
