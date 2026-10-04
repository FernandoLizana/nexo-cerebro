"""
Nexo Arena — escenarios reproducibles Level 2.

Agency: los escenarios miden aprendizaje; nunca escriben choice_key.
"""

from __future__ import annotations

from .task_discrimination import run_discrimination_good_vs_dry
from .task_dry_fountain import run_dry_fountain_failure
from .task_hunger_unknown_bowl import run_hunger_unknown_bowl_arm
from .task_hygiene_unknown_bath import run_hygiene_unknown_bath_arm
from .task_physics_locomotion import run_physics_locomotion_smoke
from .task_thirst_unknown_water import run_thirst_unknown_water_arm, summarize_thirst_rows
from .task_transfer_fountain import run_transfer_fountain_arm

__all__ = [
    "run_thirst_unknown_water_arm",
    "summarize_thirst_rows",
    "run_hunger_unknown_bowl_arm",
    "run_dry_fountain_failure",
    "run_transfer_fountain_arm",
    "run_hygiene_unknown_bath_arm",
    "run_physics_locomotion_smoke",
    "run_discrimination_good_vs_dry",
]
