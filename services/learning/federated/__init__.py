"""Federated learning research sandbox (S17).

Explicit opt-in only. Never enabled by default. Not a production deploy path.
"""

from __future__ import annotations

from services.learning.federated.service import FederatedResearchError, FederatedResearchService

__all__ = ["FederatedResearchError", "FederatedResearchService"]
