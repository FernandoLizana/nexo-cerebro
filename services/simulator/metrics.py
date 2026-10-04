"""Throughput / memory / social-graph metrics for the Swarm Simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimMetrics:
    """Simulation metrics — NOT evidence of real multi-device networking."""

    nodes: int = 0
    beings: int = 0
    events_processed: int = 0
    sim_time: float = 0.0
    wall_seconds: float = 0.0
    peak_queue: int = 0
    estimated_bytes: int = 0
    memory_budget_bytes: int = 0
    within_memory_budget: bool = True
    interactions: int = 0
    social_edges: int = 0
    mean_degree: float = 0.0
    max_degree: int = 0
    disclaimer: str = (
        "These figures are discrete-event simulation loads. "
        "They do not prove internet-scale or multi-device networking."
    )
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def events_per_sim_unit(self) -> float:
        if self.sim_time <= 0:
            return float(self.events_processed)
        return self.events_processed / self.sim_time

    @property
    def events_per_wall_second(self) -> float:
        if self.wall_seconds <= 0:
            return float(self.events_processed)
        return self.events_processed / self.wall_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "beings": self.beings,
            "events_processed": self.events_processed,
            "sim_time": self.sim_time,
            "wall_seconds": self.wall_seconds,
            "events_per_sim_unit": self.events_per_sim_unit,
            "events_per_wall_second": self.events_per_wall_second,
            "peak_queue": self.peak_queue,
            "estimated_bytes": self.estimated_bytes,
            "memory_budget_bytes": self.memory_budget_bytes,
            "within_memory_budget": self.within_memory_budget,
            "interactions": self.interactions,
            "social_edges": self.social_edges,
            "mean_degree": self.mean_degree,
            "max_degree": self.max_degree,
            "disclaimer": self.disclaimer,
            **dict(self.extras),
        }


def load_curve_table() -> list[dict[str, Any]]:
    """Documented expected load envelopes before any internet lab (S11 acceptance).

    Values are planning envelopes for the in-process discrete-event engine,
    not measured production SLAs.
    """
    return [
        {
            "logical_nodes": 10,
            "beings_per_node": 2,
            "horizon": 50.0,
            "expected_peak_queue": 64,
            "memory_budget_bytes": 2_000_000,
            "note": "smoke / CI default",
        },
        {
            "logical_nodes": 100,
            "beings_per_node": 2,
            "horizon": 100.0,
            "expected_peak_queue": 512,
            "memory_budget_bytes": 8_000_000,
            "note": "small lab rehearsal",
        },
        {
            "logical_nodes": 1_000,
            "beings_per_node": 2,
            "horizon": 50.0,
            "expected_peak_queue": 4_096,
            "memory_budget_bytes": 64_000_000,
            "note": "stress rehearsal",
        },
        {
            "logical_nodes": 10_000,
            "beings_per_node": 1,
            "horizon": 20.0,
            "expected_peak_queue": 16_384,
            "memory_budget_bytes": 256_000_000,
            "note": "upper logical target; still one process",
        },
    ]


def social_degree_stats(adjacency: dict[str, set[str]]) -> tuple[float, int, int]:
    """Return (mean_degree, max_degree, undirected_edge_count)."""
    if not adjacency:
        return 0.0, 0, 0
    degrees = [len(v) for v in adjacency.values()]
    # Undirected: each edge counted twice in degree sum
    edge_count = sum(degrees) // 2
    mean = sum(degrees) / len(degrees)
    return float(mean), int(max(degrees) if degrees else 0), int(edge_count)
