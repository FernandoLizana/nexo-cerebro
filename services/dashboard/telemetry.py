"""Read-only telemetry snapshots for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.simulator.engine import DiscreteEventSimulator


# Paths / verbs the UI must never expose as writable control plane.
FORBIDDEN_CONTROL_ACTIONS: frozenset[str] = frozenset(
    {
        "dispatch_job",
        "EXECUTE_SHELL",
        "execute_shell",
        "create_job",
        "run_job",
        "inject_job",
        "open_shell",
        "install_package",
    }
)


@dataclass
class TelemetryHub:
    """Holds optional live simulator state for visualization."""

    simulator: DiscreteEventSimulator | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def attach_simulator(self, sim: DiscreteEventSimulator) -> None:
        self.simulator = sim

    def overview(self) -> dict[str, Any]:
        base: dict[str, Any] = {
            "mode": "read_only",
            "networking_enabled": False,
            "job_injection_enabled": False,
            "bind_policy": "loopback_preferred",
            "control_actions_forbidden": sorted(FORBIDDEN_CONTROL_ACTIONS),
        }
        if self.simulator is None:
            base["simulator"] = None
            return base
        status = self.simulator.status()
        metrics = self.simulator.metrics().to_dict()
        base["simulator"] = {
            "nodes": metrics["nodes"],
            "beings": metrics["beings"],
            "events_processed": metrics["events_processed"],
            "interactions": metrics["interactions"],
            "social_edges": metrics["social_edges"],
            "mean_degree": metrics["mean_degree"],
            "max_degree": metrics["max_degree"],
            "estimated_bytes": metrics["estimated_bytes"],
            "within_memory_budget": metrics["within_memory_budget"],
            "disclaimer": metrics["disclaimer"],
            "backend": status.get("backend"),
        }
        base["extras"] = dict(self.extras)
        return base

    def graph(self) -> dict[str, Any]:
        """Node-link JSON suitable for SVG rendering."""
        if self.simulator is None:
            return {"nodes": [], "links": [], "source": "empty"}
        nodes: list[dict[str, Any]] = []
        links: list[dict[str, Any]] = []
        for nid, node in self.simulator.nodes.items():
            nodes.append(
                {
                    "id": nid,
                    "kind": "NODE",
                    "beings": len(node.beings),
                    "heartbeats": node.heartbeats,
                    "interactions": node.interactions,
                }
            )
            for nb in node.neighbors:
                # Undirected visual: only emit when source < target
                if nid < nb:
                    links.append({"source": nid, "target": nb, "relation": "NEIGHBOR"})
        # Being interaction edges from KG
        for edge in self.simulator.graph.find_edges(relation="INTERACTED_WITH"):
            links.append(
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "relation": "INTERACTED_WITH",
                    "confidence": edge.confidence,
                }
            )
            for bid in (edge.source_id, edge.target_id):
                if not any(n["id"] == bid for n in nodes):
                    nodes.append({"id": bid, "kind": "BEING", "beings": 0})
        return {
            "nodes": nodes,
            "links": links,
            "source": "simulator",
            "read_only": True,
        }
