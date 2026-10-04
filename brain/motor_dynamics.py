"""
Dinámica motora y encarnación — Bloque I (items 85–92).

Motor continuo, cerebelo, habitización, fatiga, 2.5D, somático, alimento y escritorio.
Nunca escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .experiment_flags import get_flags


@dataclass
class EmbodiedMotorStack:
    action_counts: dict[str, int] = field(default_factory=dict)
    cerebellum_error: float = 0.0
    last_motor: list[int] = field(default_factory=list)
    food_ticks: int = 0
    somatic_ticks: int = 0
    depth_z: float = 0.0
    last_metrics: dict[str, Any] = field(default_factory=dict)

    def bind_continuous_motor(self, brain) -> None:
        """Activa política motora continua en demo (item 85)."""
        if not get_flags(brain).enable_continuous_motor:
            return
        if hasattr(brain, "motor_policy"):
            brain.motor_policy.alpha = float(np.clip(brain.motor_policy.alpha, 0.22, 0.35))

    def cerebellum_adapt(self, brain, *, planned: list[int], executed: list[int]) -> list[int]:
        """Error motor y suavizado adaptativo (item 86)."""
        if not get_flags(brain).enable_cerebellum_adaptation:
            return executed
        planned_set = set(int(m) for m in planned)
        executed_set = set(int(m) for m in executed)
        union = planned_set | executed_set
        if union:
            self.cerebellum_error = float(len(planned_set.symmetric_difference(executed_set)) / len(union))
        else:
            self.cerebellum_error = 0.0
        smoothed = brain.cerebellum.integrate(list(executed))
        if self.cerebellum_error > 0.25 and smoothed:
            # Corrección suave hacia patrón reciente estable
            smoothed = smoothed[: max(2, len(smoothed) - 1)]
        self.last_motor = list(smoothed)
        return smoothed

    def basal_habituation(self, brain, contestants: list) -> int:
        """Acciones repetidas reducen costo Go (más automáticas) — item 87."""
        if not get_flags(brain).enable_basal_habituation:
            return 0
        key = str(getattr(brain.deliberation.last, "choice_key", "") or "")
        if not key:
            return 0
        self.action_counts[key] = int(self.action_counts.get(key, 0)) + 1
        n = self.action_counts[key]
        if n < 2:
            return 0
        boost = float(np.clip(0.025 * min(n, 24), 0, 0.12))
        for c in contestants:
            if c.key == key:
                c.habit = float(np.clip(c.habit + boost, 0, 1.2))
                c.go = float(np.clip(c.go + boost * 0.65, 0, 1.25))
        bg = brain.basal_ganglia
        for idx in range(min(bg.habit.size, 6)):
            bg.habit[idx] = float(np.clip(bg.habit[idx] + boost * 0.15, 0, 3.0))
        return n

    def couple_fatigue_circadian(self, brain) -> dict[str, float]:
        """Fatiga muscular acoplada a biomecánica y reloj (item 88)."""
        if not get_flags(brain).enable_muscular_fatigue:
            return {}
        bio = brain.biomech
        hour = int(getattr(brain.world.clock, "hour", 12))
        night = hour >= 22 or hour < 6
        exertion = float(bio.activity_strain()[0]) if hasattr(bio, "activity_strain") else 0.1
        bio.physical_fatigue = float(
            np.clip(bio.physical_fatigue + exertion * 0.01 * (1.15 if night else 1.0), 0, 1)
        )
        recovery = 0.012 if night and bio.physical_fatigue > 0.2 else 0.005
        if get_flags(brain).enable_circadian and 6 <= hour <= 10:
            recovery += 0.004
        bio.physical_fatigue = float(np.clip(bio.physical_fatigue - recovery, 0, 1))
        bio.apply_to_interoception(brain.body, brain.nociceptor)
        return {
            "physical_fatigue": round(bio.physical_fatigue, 3),
            "body_fatigue": round(brain.body.fatigue, 3),
            "hour": hour,
        }

    def update_world_depth(self, brain) -> float:
        """Sincroniza elevación 2.5D agente↔mundo (item 89)."""
        if not get_flags(brain).enable_world_depth:
            return 0.0
        z = float(getattr(brain.biomech, "height", 0.0))
        self.depth_z = z
        if hasattr(brain.world, "agent_z"):
            brain.world.agent_z = z
        return z

    def tick_somatic_passive(self, brain) -> dict[str, Any] | None:
        """Contacto pasivo ampliado (sofá, TV, estufa…) — item 90."""
        if not get_flags(brain).enable_somatic_passive:
            return None
        from .somatic_affordances import apply_somatic_contact

        contact = apply_somatic_contact(brain.world, brain.body, nociceptor=brain.nociceptor)
        if contact:
            self.somatic_ticks += 1
        return contact

    def tick_food_cycle(self, brain) -> dict[str, Any]:
        """Ciclo jardín→despensa→cocina→metabolismo (item 91)."""
        if not get_flags(brain).enable_food_cycle:
            return {}
        from .food_system import ensure_garden_crops, ensure_stove, tick_crops

        ensure_garden_crops(brain.world)
        ensure_stove(brain.world)
        tick_crops(brain.world)
        self.food_ticks += 1
        pantry = brain.world.pantry
        metabolism = 0.0
        if pantry and brain.body.satiety > 0.35:
            metabolism = float(np.clip(0.004 + brain.body.satiety * 0.003, 0, 0.02))
            brain.body.hunger = float(np.clip(brain.body.hunger + metabolism, 0, 1))
            brain.body.satiety = float(np.clip(brain.body.satiety - metabolism * 0.5, 0, 1))
        return {
            "pantry_raw": sum(1 for p in pantry if p.get("raw")),
            "pantry_cooked": sum(1 for p in pantry if not p.get("raw")),
            "metabolism": round(metabolism, 4),
            "crop_ticks": self.food_ticks,
        }

    def resolve_desk_study(self, brain, *, choice_key: str = "", curiosity: float = 0.0) -> dict[str, Any]:
        """Estudio en escritorio determinista desde PFC + progreso (item 92)."""
        if not get_flags(brain).enable_desk_study_deterministic:
            return {}
        from .behavior_integration import pick_desk_study_event

        return pick_desk_study_event(brain, choice_key=choice_key, curiosity=curiosity)

    def post_motor(
        self,
        brain,
        *,
        planned_motor: list[int] | None = None,
        executed_motor: list[int] | None = None,
        choice_key: str = "",
        curiosity: float = 0.0,
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_motor_dynamics:
            return {}
        metrics: dict[str, Any] = {}
        if flags.enable_continuous_motor:
            self.bind_continuous_motor(brain)
        if flags.enable_cerebellum_adaptation and executed_motor is not None:
            adapted = self.cerebellum_adapt(
                brain,
                planned=list(planned_motor or []),
                executed=list(executed_motor),
            )
            metrics["cerebellum"] = {
                "error": round(self.cerebellum_error, 4),
                "motor": adapted,
            }
        if flags.enable_muscular_fatigue:
            metrics["fatigue"] = self.couple_fatigue_circadian(brain)
        if flags.enable_world_depth:
            metrics["depth_z"] = round(self.update_world_depth(brain), 3)
        if flags.enable_somatic_passive:
            metrics["somatic"] = self.tick_somatic_passive(brain)
        if flags.enable_food_cycle:
            metrics["food"] = self.tick_food_cycle(brain)
        if flags.enable_desk_study_deterministic and choice_key in (
            "study", "research", "clinical", "biopsych", "infant"
        ):
            metrics["desk_study"] = self.resolve_desk_study(
                brain, choice_key=choice_key, curiosity=curiosity
            )
        self.last_metrics = metrics
        return metrics

    def to_dict(self) -> dict[str, Any]:
        top_actions = sorted(self.action_counts.items(), key=lambda x: -x[1])[:6]
        return {
            "cerebellum_error": round(self.cerebellum_error, 4),
            "depth_z": round(self.depth_z, 3),
            "action_counts": dict(top_actions),
            "food_ticks": self.food_ticks,
            "somatic_ticks": self.somatic_ticks,
            "last_motor": self.last_motor,
            "metrics": self.last_metrics,
            "agency_note": "Motor stack biases movement only; PFC selects choice_key",
        }
