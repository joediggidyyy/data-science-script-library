from __future__ import annotations

import json
from pathlib import Path

from conftest import import_module_from_path, scripts_root


def test_run_benchmarks_returns_expected_sections(tmp_path: Path) -> None:
    script = scripts_root() / "benchmarks" / "benchmark_simulator.py"
    mod = import_module_from_path("benchmark_simulator_mod", script)

    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
                "edges": [
                    {"source": "a", "target": "b"},
                    {"source": "b", "target": "c"},
                ],
            }
        ),
        encoding="utf-8",
    )

    results = mod.run_benchmarks(
        graph_path=graph_path,
        random_access_iterations=25,
        neighbor_traversal_iterations=20,
        path_finding_iterations=10,
        max_depth=2,
        as_json=True,
    )

    assert results["nodes"] == 3
    assert results["edges"] == 2
    assert "random_access" in results
    assert "neighbor_traversal" in results
    assert "path_finding" in results
    assert 0.0 <= results["random_access"]["success_rate"] <= 1.0
    assert 0.0 <= results["path_finding"]["success_rate"] <= 1.0
