from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def public_repo_root() -> Path:
    # .../projects/data-science-script-library/tests/conftest.py -> repo root is parent
    return Path(__file__).resolve().parent.parent


def scripts_root() -> Path:
    return public_repo_root() / "scripts"


def import_module_from_path(module_name: str, path: Path) -> ModuleType:
    """Import a Python module from an arbitrary file path.

    These public scripts are intentionally not packaged; this loader lets us
    test them without requiring package installation.
    """

    path = Path(path)
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {path}")

    module = importlib.util.module_from_spec(spec)
    # Some stdlib features (notably `dataclasses`) expect the module to be
    # present in sys.modules during class decoration/execution.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module
