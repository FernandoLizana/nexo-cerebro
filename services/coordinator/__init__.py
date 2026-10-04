"""NEXO Swarm Coordinator (S7) — registry & job routing only.

Does NOT run cognition. Does NOT execute shell. In-process control plane for S7;
TLS multi-device networking is deferred to later phases.
"""

from __future__ import annotations

from services.coordinator.service import Coordinator, CoordinatorError

__all__ = ["Coordinator", "CoordinatorError"]
