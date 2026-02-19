# Contributing

Thanks for helping improve this scripts library.

## Goals

- Keep scripts *standalone* and easy to run.
- Prefer clear CLI interfaces (argparse) and good error messages.
- Avoid hardcoding environment-specific paths.
- Never include secrets in the repository.

## Development setup

- Create a virtual environment
- Install dependencies from `requirements.txt` (core) or `requirements-full.txt` (all optional features)
- Run the script you are working on against small sample inputs

Suggested commands (from the script-library folder):

```text
pip install -r requirements.txt
pytest
```

If you are working on TensorFlow-class coursework, use Python 3.13 with:

```text
python scripts/repo/setup/setup_student_env.py --deps tensorflow-class --python <python3.13>
```

Before opening a PR, also run:

```text
python maintain.py
```

This keeps public quality artifacts current and catches maintenance regressions early.

## Style

- Keep scripts readable and beginner-friendly
- Include a module docstring describing what the script does
- Include example usage in `README.md`

---

If you add a new script, please also add it to the top-level `README.md` index.

> This Repository is Maintained _by CodeSentinel_
