"""Metabolismo basal y costos por acción."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.body.body_state import ActionCost, VirtualBody


@dataclass
class MetabolismEngine:
    """Tasa metabólica basal calibrada para ticks simulados."""

    basal_energy_drain: float = 0.0006
    basal_hydration_drain: float = 0.0003
    fatigue_recovery_resting: float = 0.0002
    fatigue_accumulation: float = 0.0004
    sleep_pressure_rate: float = 0.0005
    circadian_fatigue_multiplier: float = 1.0

    def tick_basal(self, body: VirtualBody) -> dict[str, float]:
        """Deltas homeostáticos por tick sin acción."""
        energy_delta = -self.basal_energy_drain * self.circadian_fatigue_multiplier
        hydration_delta = -self.basal_hydration_drain
        fatigue_delta = self.fatigue_accumulation - self.fatigue_recovery_resting
        sleep_delta = self.sleep_pressure_rate + body.fatigue * 0.0003

        body.energy += energy_delta
        body.hydration += hydration_delta
        body.fatigue += fatigue_delta
        body.sleep_pressure = min(1.0, body.sleep_pressure + sleep_delta)

        if body.energy < 0.3:
            body.stress_load = min(1.0, body.stress_load + 0.001)
        if body.pain > 0.3:
            body.stress_load = min(1.0, body.stress_load + 0.002)
        body.clamp()
        return {
            "energy": energy_delta,
            "hydration": hydration_delta,
            "fatigue": fatigue_delta,
            "sleep_pressure": sleep_delta,
        }

    def apply_action(self, body: VirtualBody, action: str) -> dict[str, float]:
        costs = VirtualBody.action_costs()
        cost = costs.get(action, ActionCost())
        pre_energy = body.energy
        body.apply_cost(cost)
        if action == "eat":
            body.energy = min(1.0, body.energy + 0.22)
            body.hydration = min(1.0, body.hydration + 0.05)
            body.social_need = max(0.0, body.social_need - 0.05)
        elif action == "rest":
            body.fatigue = max(0.0, body.fatigue - 0.06)
            body.sleep_pressure = max(0.0, body.sleep_pressure - 0.04)
        elif action == "approach_caregiver":
            body.social_need = max(0.0, body.social_need - 0.12)
            body.stress_load = max(0.0, body.stress_load - 0.03)
        body.clamp()
        return {
            "energy": body.energy - pre_energy,
            "fatigue": cost.fatigue,
            "action": action,
        }
