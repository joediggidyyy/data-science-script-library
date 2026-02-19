from __future__ import annotations

import json
from pathlib import Path

from conftest import public_repo_root


def test_first_week_lab_template_has_valid_structure() -> None:
    path = public_repo_root() / "notebooks" / "first_week_lab_template.ipynb"
    assert path.exists(), "first_week_lab_template.ipynb is missing"

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("nbformat") == 4
    assert isinstance(payload.get("cells"), list)
    assert len(payload["cells"]) >= 3

    for idx, cell in enumerate(payload["cells"], start=1):
        assert isinstance(cell, dict), f"cell {idx} is not an object"
        assert cell.get("cell_type") in {"markdown", "code"}, f"cell {idx} has unexpected type"
        assert isinstance(cell.get("metadata"), dict), f"cell {idx} missing metadata"
        assert isinstance(cell.get("source"), list), f"cell {idx} missing source lines"
