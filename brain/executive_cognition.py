"""
Cognición ejecutiva ampliada — Bloque D (items 33–44).

Atención, consciencia, metacognición, Stroop, set-shifting, DMN.
Sesga deliberación y WM; nunca escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .experiment_flags import get_flags


@dataclass
class DualTaskMonitor:
    """Interferencia WM + demanda motora (paradigma doble tarea)."""

    wm_load: float = 0.0
    motor_load: float = 0.0
    interference: float = 0.0
    agency_penalty: float = 0.0

    def measure(self, brain, *, motor_active: bool = False) -> dict[str, float]:
        cap = max(1, brain.working_memory.effective_capacity())
        wm_n = len(brain.working_memory.slots)
        self.wm_load = float(np.clip(wm_n / cap, 0, 1.2))
        self.motor_load = 1.0 if motor_active else 0.35
        self.interference = float(np.clip(self.wm_load * 0.55 + self.motor_load * 0.35, 0, 1))
        self.agency_penalty = float(np.clip(self.interference * 0.12, 0, 0.15))
        return {
            "wm_load": round(self.wm_load, 3),
            "motor_load": round(self.motor_load, 3),
            "interference": round(self.interference, 3),
            "agency_penalty": round(self.agency_penalty, 3),
        }


@dataclass
class StroopController:
    """Inhibición prepotente — impulso límbico vs meta PFC."""

    last_conflict: float = 0.0
    inhibited_key: str = ""
    stroop_active: bool = False

    def apply(
        self,
        contestants: list,
        *,
        limbic_top,
        pfc_top,
        goal_key: str | None,
    ) -> None:
        self.stroop_active = False
        self.inhibited_key = ""
        if not goal_key or limbic_top.key == pfc_top.key:
            self.last_conflict = 0.0
            return
        if limbic_top.limbic > 0.35 and pfc_top.pfc > 0.25 and limbic_top.key != goal_key:
            self.last_conflict = float(
                np.clip((limbic_top.limbic - pfc_top.pfc * 0.5) * 0.8, 0, 0.85)
            )
            self.stroop_active = True
            self.inhibited_key = limbic_top.key
            for c in contestants:
                if c.key == limbic_top.key:
                    c.no_go = float(c.no_go + self.last_conflict * 0.35)
                    c.net = float(c.go - c.no_go)


@dataclass
class SetShiftingController:
    """Flexibilidad cognitiva — costo al cambiar de schema."""

    last_schema: str = ""
    switch_count: int = 0
    switch_cost: float = 0.0

    def note_choice(self, choice_key: str) -> float:
        cost = 0.0
        if self.last_schema and choice_key != self.last_schema:
            self.switch_count += 1
            cost = float(np.clip(0.08 + self.switch_count * 0.015, 0.08, 0.22))
            self.switch_cost = cost
        else:
            self.switch_cost *= 0.92
        self.last_schema = choice_key
        return cost

    def apply_penalty(self, brain, choice_key: str) -> None:
        cost = self.note_choice(choice_key)
        if cost > 0.05:
            brain.deliberation.set_penalty(choice_key, cost * 0.5)


@dataclass
class DefaultModeNetwork:
    """Replay interno en reposo — baja demanda externa."""

    active: bool = False
    last_replay: str = ""
    replay_count: int = 0

    def tick(self, brain, *, drives: dict, surprise: float) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_dmn_replay:
            self.active = False
            return {"active": False}
        peak = max(drives.values()) if drives else 0.0
        if peak > 0.38 or surprise > 0.42 or brain.brainstem.sleep_pressure > 0.55:
            self.active = False
            return {"active": False}
        self.active = True
        mem = None
        if brain.hippocampus.size > 0:
            mem = brain.hippocampus.sample_for_replay(
                sleep_pressure=brain.brainstem.sleep_pressure * 0.3,
                modulators=brain.modulators,
                sleep_phase="awake",
                replay_mode="selective",
            )
        if mem:
            lbl = str(mem.get("label", "recuerdo"))[:56]
            self.last_replay = lbl
            self.replay_count += 1
            brain.working_memory.push(
                label=f"DMN: {lbl}",
                modality="internal",
                room=brain.world.current_room(),
                tags=["dmn", "replay"],
                salience=0.42,
                valence=float(mem.get("valence", 0)),
            )
            brain.modulators.acetylcholine = float(
                np.clip(brain.modulators.acetylcholine - 0.02, 0.08, 1)
            )
        return {
            "active": True,
            "last_replay": self.last_replay,
            "replay_count": self.replay_count,
        }


@dataclass
class ExecutiveCognitionStack:
    dual_task: DualTaskMonitor = field(default_factory=DualTaskMonitor)
    stroop: StroopController = field(default_factory=StroopController)
    set_shift: SetShiftingController = field(default_factory=SetShiftingController)
    dmn: DefaultModeNetwork = field(default_factory=DefaultModeNetwork)
    last_metrics: dict[str, Any] = field(default_factory=dict)

    def pre_deliberation(
        self,
        brain,
        *,
        drives: dict,
        surprise: float,
        attended: list[dict],
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_executive_cognition:
            return {}
        dmn_out = self.dmn.tick(brain, drives=drives, surprise=surprise)
        self.last_metrics = {"dmn": dmn_out}
        return self.last_metrics

    def post_deliberation(
        self,
        brain,
        *,
        contestants: list | None = None,
        limbic_top=None,
        pfc_top=None,
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_executive_cognition:
            return {}
        delib = brain.deliberation.last
        motor_active = delib.choice_key not in ("", "wait", "idle", "rest", "think")
        dual: dict[str, float] = {}
        if get_flags(brain).enable_dual_task_metrics:
            dual = self.dual_task.measure(brain, motor_active=motor_active)

        if flags.enable_set_shifting:
            self.set_shift.note_choice(delib.choice_key or "")

        if flags.enable_metacognition_calibration and brain.consciousness.metacognition:
            mc = brain.consciousness.metacognition
            clarity = float(mc.get("clarity", 0.5))
            doubt = float(mc.get("doubt", 0))
            penalty = float(dual.get("agency_penalty", 0)) if dual else 0.0
            delib.confidence = float(
                np.clip(
                    delib.confidence * (0.72 + 0.28 * clarity)
                    - doubt * 0.18
                    - penalty,
                    0.1,
                    0.96,
                )
            )
            delib.agency = float(np.clip(delib.agency - penalty, 0.05, 1.0))

        if (
            flags.enable_imagination_motor
            and hasattr(brain, "imagination")
            and brain.imagination.last
        ):
            motor_act = float(brain.imagination.last.get("motor_act", 0))
            if motor_act > 0.4 and delib.choice_key:
                brain.modulators.acetylcholine = float(
                    np.clip(brain.modulators.acetylcholine + 0.015, 0, 1)
                )

        self.last_metrics.update({"dual_task": dual, "stroop": self.stroop.__dict__})
        return self.last_metrics

    def stroop_in_deliberation(
        self,
        brain,
        contestants: list,
        *,
        limbic_top,
        pfc_top,
    ) -> None:
        if not get_flags(brain).enable_stroop_inhibition:
            return
        goal = None
        if hasattr(brain, "agent_loop"):
            top = brain.agent_loop.goal_stack.peek()
            if top:
                goal = top.choice_key
        self.stroop.apply(
            contestants,
            limbic_top=limbic_top,
            pfc_top=pfc_top,
            goal_key=goal,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dual_task": {
                "wm_load": round(self.dual_task.wm_load, 3),
                "interference": round(self.dual_task.interference, 3),
            },
            "stroop": {
                "active": self.stroop.stroop_active,
                "conflict": round(self.stroop.last_conflict, 3),
                "inhibited": self.stroop.inhibited_key,
            },
            "set_shift": {
                "switches": self.set_shift.switch_count,
                "cost": round(self.set_shift.switch_cost, 3),
            },
            "dmn": {
                "active": self.dmn.active,
                "last_replay": self.dmn.last_replay,
            },
            "metrics": self.last_metrics,
        }
