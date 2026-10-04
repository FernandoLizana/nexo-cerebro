"""NEXO Swarm Simulator (S11) — discrete-event logical nodes.

Simulates 10→10 000 nodes **without** OS processes or real sockets.
Metrics are simulation loads, not proof of internet-scale networking.
"""

from __future__ import annotations

from services.simulator.engine import DiscreteEventSimulator, SimulatorError
from services.simulator.metrics import SimMetrics, load_curve_table

__all__ = [
    "DiscreteEventSimulator",
    "SimMetrics",
    "SimulatorError",
    "load_curve_table",
]
