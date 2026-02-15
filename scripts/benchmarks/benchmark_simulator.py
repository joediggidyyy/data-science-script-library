"""benchmark_simulator.py

Lightweight graph benchmark simulator.

Given a graph exported as JSON, this script runs a few simple micro-benchmarks:
- random node lookups
- neighbor traversal
- shallow path finding (BFS)

The goal is educational and practical: quantify basic latency distributions
(p50/p95/p99) and compare different graph sizes or storage representations.

Expected JSON shapes (best-effort):
- {"nodes": [...], "edges": [...]} where edges use "source"/"target"

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.

"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Optional

class GraphSimulator:
    def __init__(self, graph_path: Path):
        self.graph_path = graph_path
        self.nodes = {}
        self.edges = []
        self.adjacency = {}
        self.load_graph()

    def load_graph(self):
        start = time.perf_counter()
        with open(self.graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object with keys like 'nodes' and 'edges'.")

        nodes = data.get("nodes")
        edges = data.get("edges")

        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("Graph JSON must contain list fields 'nodes' and 'edges'.")

        # Support common id fields.
        def node_id(n: dict) -> str:
            for k in ("artifact_id", "id", "node_id", "name"):
                if k in n and n[k] is not None:
                    return str(n[k])
            raise ValueError("Node is missing an id field (expected one of: artifact_id, id, node_id, name)")

        self.nodes = {node_id(n): n for n in nodes if isinstance(n, dict)}
        self.edges = [e for e in edges if isinstance(e, dict)]
        
        # Build adjacency
        for e in self.edges:
            if "source" not in e or "target" not in e:
                continue
            src = str(e["source"])
            if src not in self.adjacency:
                self.adjacency[src] = []
            self.adjacency[src].append(e)
            
        end = time.perf_counter()
        print(f"Graph loaded in {end - start:.4f}s. Nodes: {len(self.nodes)}, Edges: {len(self.edges)}")

    def benchmark_random_access(self, iterations: int = 10000) -> Dict[str, float]:
        """Simulate random node lookups."""
        keys = list(self.nodes.keys())
        latencies = []
        success = 0
        
        for _ in range(iterations):
            target = random.choice(keys)
            start = time.perf_counter()
            node = self.nodes.get(target)
            end = time.perf_counter()
            if node:
                success += 1
            latencies.append((end - start) * 1000) # ms
            
        return {
            "p50_ms": statistics.median(latencies),
            "p95_ms": statistics.quantiles(latencies, n=20)[18],
            "p99_ms": statistics.quantiles(latencies, n=100)[98],
            "success_rate": success / iterations
        }

    def benchmark_neighbor_traversal(self, iterations: int = 5000) -> Dict[str, float]:
        """Simulate finding all neighbors of a node."""
        keys = list(self.nodes.keys())
        latencies = []
        
        for _ in range(iterations):
            target = random.choice(keys)
            start = time.perf_counter()
            neighbors = self.adjacency.get(target, [])
            # Simulate reading neighbor data
            _ = [self.nodes.get(str(e.get("target"))) for e in neighbors]
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
            
        return {
            "p50_ms": statistics.median(latencies),
            "p95_ms": statistics.quantiles(latencies, n=20)[18],
            "avg_neighbors": sum(len(self.adjacency.get(k, [])) for k in keys) / len(keys)
        }

    def benchmark_path_finding(self, iterations: int = 500, max_depth: int = 3) -> Dict[str, float]:
        """Simulate a simple BFS to find a path or reachability."""
        keys = list(self.nodes.keys())
        latencies = []
        found_count = 0
        
        for _ in range(iterations):
            start_node = random.choice(keys)
            end_node = random.choice(keys)
            
            t0 = time.perf_counter()
            # Simple BFS
            queue = [(start_node, 0)]
            visited = {start_node}
            found = False
            
            while queue:
                curr, depth = queue.pop(0)
                if curr == end_node:
                    found = True
                    break
                if depth >= max_depth:
                    continue
                
                for e in self.adjacency.get(curr, []):
                    tgt = str(e.get("target"))
                    if tgt not in visited:
                        visited.add(tgt)
                        queue.append((tgt, depth + 1))
            
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)
            if found:
                found_count += 1
                
        return {
            "p50_ms": statistics.median(latencies),
            "p95_ms": statistics.quantiles(latencies, n=20)[18],
            "success_rate": found_count / iterations
        }

def _print_section(title: str) -> None:
    print("\n--- " + title + " ---")


def run_benchmarks(
    *,
    graph_path: Path,
    random_access_iterations: int,
    neighbor_traversal_iterations: int,
    path_finding_iterations: int,
    max_depth: int,
    as_json: bool,
) -> dict[str, Any]:
    if not graph_path.exists():
        raise FileNotFoundError(graph_path)

    sim = GraphSimulator(graph_path)

    results: dict[str, Any] = {"graph": str(graph_path), "nodes": len(sim.nodes), "edges": len(sim.edges)}

    ra = sim.benchmark_random_access(iterations=random_access_iterations)
    nt = sim.benchmark_neighbor_traversal(iterations=neighbor_traversal_iterations)
    pf = sim.benchmark_path_finding(iterations=path_finding_iterations, max_depth=max_depth)

    results["random_access"] = ra
    results["neighbor_traversal"] = nt
    results["path_finding"] = pf

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        _print_section(f"Random Access ({random_access_iterations} ops)")
        print(json.dumps(ra, indent=2))

        _print_section(f"Neighbor Traversal ({neighbor_traversal_iterations} ops)")
        print(json.dumps(nt, indent=2))

        _print_section(f"Path Finding (depth {max_depth}, {path_finding_iterations} ops)")
        print(json.dumps(pf, indent=2))

    return results


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run lightweight graph micro-benchmarks on a graph JSON")
    parser.add_argument("--graph", required=True, help="Path to graph JSON file")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducibility")
    parser.add_argument("--random-access", type=int, default=10_000, help="Iterations for random-access benchmark")
    parser.add_argument("--neighbor-traversal", type=int, default=5_000, help="Iterations for neighbor traversal benchmark")
    parser.add_argument("--path-finding", type=int, default=500, help="Iterations for path finding benchmark")
    parser.add_argument("--max-depth", type=int, default=3, help="Max BFS depth for path finding")
    parser.add_argument("--json", action="store_true", help="Emit a single JSON payload (machine-readable)")

    args = parser.parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)

    run_benchmarks(
        graph_path=Path(args.graph).resolve(),
        random_access_iterations=args.random_access,
        neighbor_traversal_iterations=args.neighbor_traversal,
        path_finding_iterations=args.path_finding,
        max_depth=args.max_depth,
        as_json=args.json,
    )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
