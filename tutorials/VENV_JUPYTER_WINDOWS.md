# Windows (PC): venv + Jupyter in VS Code

This guide is for Windows students using PowerShell or Command Prompt.

## Step 1: Open the project folder

Open a terminal in `projects/data-science-script-library`.

## Step 2: Create a virtual environment

```text
python -m venv .venv
```

## Step 3: Activate the virtual environment

PowerShell:

```text
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```text
.venv\Scripts\activate.bat
```

## Step 4: Install dependencies

Core:

```text
pip install -r requirements.txt
```

Full:

```text
pip install -r requirements-full.txt
```

## Step 5: Install Jupyter support

```text
pip install ipykernel jupyter
python -m ipykernel install --user --name dssl --display-name "Python (data-science-script-library)"
```

## Step 6: Configure VS Code

1. Install extensions: Python + Jupyter.
2. Run "Python: Select Interpreter" and choose `.venv`.
3. Open/create a notebook.
4. Pick kernel: **Python (data-science-script-library)**.

## Step 7: Verify kernel

Run:

```python
import sys
print(sys.executable)
```

You should see a path inside `.venv`.

## Optional automation

Non-interactive setup:

```text
python scripts/repo/setup/setup_student_env.py
```

Prompt-driven setup:

```text
python scripts/repo/setup/setup_student_env.py --interactive
```

TensorFlow class profile (Python 3.13 required):

```text
python scripts/repo/setup/setup_student_env.py --deps tensorflow-class --python C:\\Path\\To\\Python313\\python.exe
```

After setup, open:

- `notebooks/first_week_lab.ipynb`

Reference template:

- `notebooks/first_week_lab_template.ipynb`
