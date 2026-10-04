"""NEXO Swarm Dashboard (S12) — local read-only scientific telemetry.

Binds to loopback by default. Does not dispatch jobs or run cognition.
"""

from __future__ import annotations

from services.dashboard.app import create_app
from services.dashboard.auth import LocalDashboardAuth, DashboardAuthError

__all__ = ["DashboardAuthError", "LocalDashboardAuth", "create_app"]
