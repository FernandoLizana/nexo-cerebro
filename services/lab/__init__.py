"""NEXO multi-device lab toolkit (S15).

Voluntary lab rehearsals, reproducible experiment IDs, TLS policy, kill-switch checks.
Does not enable arbitrary remote code execution.
"""

from __future__ import annotations

from services.lab.experiment_id import make_experiment_id
from services.lab.session import MultiDeviceLabSession, LabError

__all__ = ["LabError", "MultiDeviceLabSession", "make_experiment_id"]
