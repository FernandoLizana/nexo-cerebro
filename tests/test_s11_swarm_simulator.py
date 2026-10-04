"""S11 — Swarm Simulator tests (budgets, social stats, no networking)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.simulator.engine import DiscreteEventSimulator, SimulatorError
from services.simulator.metrics import load_curve_table

ROOT = Path(__file__).resolve().parents[1]
SIM_PKG = ROOT / "services" / "simulator"


def test_small_run_within_memory_and_social_stats() -> None:
    sim = DiscreteEventSimulator(
        n_nodes=10,
        beings_per_node=2,
        seed=7,
        memory_budget_bytes=2_000_000,
        avg_degree=3,
    )
    sim.seed_workload(horizon=50.0, interacts_per_node=3)
    metrics = sim.run_until(50.0)
    assert metrics.events_processed > 0
    assert metrics.within_memory_budget is True
    assert metrics.nodes == 10
    assert metrics.beings == 20
    assert metrics.interactions >= 1
    assert metrics.social_edges >= 1
    assert metrics.mean_degree >= 0.0
    assert "simulation" in metrics.disclaimer.lower() or "not prove" in metrics.disclaimer.lower()
    assert sim.status()["networking_enabled"] is False
    assert sim.status()["os_processes_per_node"] is False


def test_throughput_and_peak_queue_recorded() -> None:
    sim = DiscreteEventSimulator(n_nodes=50, beings_per_node=1, seed=1, memory_budget_bytes=8_000_000)
    sim.seed_workload(horizon=30.0, interacts_per_node=2)
    m = sim.run_until(30.0)
    assert m.peak_queue >= 1
    assert m.events_per_wall_second > 0
    assert m.estimated_bytes > 0


def test_load_curve_table_documents_envelopes() -> None:
    table = load_curve_table()
    assert len(table) >= 4
    sizes = [row["logical_nodes"] for row in table]
    assert 10 in sizes and 10_000 in sizes
    for row in table:
        assert row["memory_budget_bytes"] > 0
        assert row["expected_peak_queue"] > 0


def test_hard_cap_and_no_sockets_in_package() -> None:
    with pytest.raises(SimulatorError, match="safety cap"):
        DiscreteEventSimulator(n_nodes=50_001)
    for path in SIM_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"socket", "subprocess", "requests"}
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {"socket", "subprocess", "requests"}


def test_reproducible_with_seed() -> None:
    def run(seed: int):
        sim = DiscreteEventSimulator(n_nodes=20, beings_per_node=2, seed=seed)
        sim.seed_workload(horizon=40.0, interacts_per_node=2)
        return sim.run_until(40.0)

    a = run(99)
    b = run(99)
    assert a.events_processed == b.events_processed
    assert a.interactions == b.interactions
    assert a.social_edges == b.social_edges
