# Virtual Environments + Jupyter in VS Code (Student Hub)

This is the main onboarding hub for setting up:

1. a Python virtual environment (`venv`)
2. Jupyter notebooks in VS Code
3. optional automated setup scripts

Audience: computer science students (beginner-friendly).

---

## Choose your operating system guide

- **Windows (PC):** `tutorials/VENV_JUPYTER_WINDOWS.md`
- **macOS:** `tutorials/VENV_JUPYTER_MACOS.md`
- **Linux:** `tutorials/VENV_JUPYTER_LINUX.md`

These guides are split to avoid OS-command confusion.

---

## OS-agnostic automated setup (recommended)

Use the cross-platform setup script from repository root:

```text
python scripts/repo/setup/setup_student_env.py
```

Default behavior (non-interactive):

- creates a local `.venv`
- installs core dependencies
- installs Jupyter tooling (`ipykernel`, `jupyter`)
- registers a notebook kernel for VS Code
- creates `notebooks/first_week_lab.ipynb`

Template source tracked in repo:

- `notebooks/first_week_lab_template.ipynb`

Useful options:

```text
python scripts/repo/setup/setup_student_env.py --deps full
python scripts/repo/setup/setup_student_env.py --deps tensorflow-class --python /path/to/python3.13
python scripts/repo/setup/setup_student_env.py --dry-run
python scripts/repo/setup/setup_student_env.py --interactive
```

### TensorFlow classes (Python 3.13)

For courses that require TensorFlow on Python 3.13, use the `tensorflow-class` profile and pass a Python 3.13 interpreter via `--python` if needed.

### Interactive mode

Use `--interactive` for prompt-driven setup. This mode is designed for students with limited command-line experience.

---

## Minimum VS Code checklist (all OSes)

1. Open this folder in VS Code.
2. Install extensions:
   - Python (Microsoft)
   - Jupyter (Microsoft)
3. Select your `.venv` interpreter.
4. Open a notebook and select the project kernel.
5. Run a quick check cell:

```python
import sys
print(sys.executable)
```

---

## Troubleshooting (all OSes)

- If packages install globally, your venv is not active.
- If VS Code uses the wrong interpreter, run "Python: Select Interpreter" again.
- If kernel is missing, rerun kernel registration from the activated venv.
