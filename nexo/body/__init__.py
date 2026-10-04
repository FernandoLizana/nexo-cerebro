"""Cuerpo virtual del agente integrado."""

from __future__ import annotations

from nexo.body.body_state import ActionCost, VirtualBody
from nexo.body.interoception import InteroceptiveChannel, InteroceptiveSignal
from nexo.body.metabolism import MetabolismEngine

__all__ = [
    "ActionCost",
    "InteroceptiveChannel",
    "InteroceptiveSignal",
    "MetabolismEngine",
    "VirtualBody",
]
