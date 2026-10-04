"""Procesos Sprint 6 — neuromodulación, TD learning y plasticidad."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.homeostasis.drives import DriveField
from nexo.neuromodulation.state import NeuromodulatorState
from nexo.reinforcement.td_learning import TDRewardSystem


PLASTIC_EDGES: tuple[tuple[str, str], ...] = (
    ("prefrontal", "basal_ganglia"),
    ("hippocampus", "prefrontal"),
    ("neuromodulation", "hippocampus"),
    ("visual_cortex", "posterior_parietal"),
)


def _energy_bucket(energy: float) -> int:
    return int(max(0, min(7, energy * 8)))


def _top_drive(drives: DriveField | None) -> str:
    if drives is None or not drives.drives:
        return "?"
    return max(drives.drives.items(), key=lambda x: x[1])[0]


@dataclass
class TDBiasProcess(BaseProcess):
    """Expone sesgos Go TD antes de selección de acción."""

    process_id: str = "td_bias"
    period_ticks: int = 1
    priority: int = 61

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        td: TDRewardSystem | None = context.config.get("td_system")
        drives: DriveField | None = context.config.get("drives")
        if world is None or td is None:
            return []

        deliberation = context.config.get("deliberation_result")
        conflict = float(getattr(deliberation, "conflict", 0.0)) if deliberation else 0.0
        energy = context.state_store.state.homeostatic.energy
        biases = td.go_biases(
            top_drive=_top_drive(drives),
            energy_bucket=_energy_bucket(energy),
            action_keys=world.available_actions(),
            conflict=conflict,
        )
        context.config["td_go_biases"] = biases
        if not biases:
            return []
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="td.bias_computed",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload={"biases": {k: round(v, 5) for k, v in biases.items()}},
            )
        ]


@dataclass
class NeuromodulatorUpdateProcess(BaseProcess):
    """Actualiza neuromoduladores tras recompensa y sorpresa."""

    process_id: str = "neuromodulator_update"
    period_ticks: int = 1
    priority: int = 54

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        mods: NeuromodulatorState = context.config.setdefault("modulators", NeuromodulatorState())
        recent = context.state_store.event_log[-8:]
        reward_ev = next((e for e in reversed(recent) if e.event_type == "reward.received"), None)
        if reward_ev is None:
            return []

        reward = float(reward_ev.payload.get("value", 0.0))
        state = context.state_store.state
        h = state.homeostatic
        surprises = context.config.get("surprises") or {}
        novelty = float(sum(surprises.values()) / len(surprises)) if surprises else 0.0
        attention = min(1.0, len(state.attention_focus) * 0.25)

        snap = mods.update(
            reward=reward,
            stress=h.stress_load,
            novelty=novelty,
            attention=attention,
            sleep_pressure=h.sleep_pressure,
        )
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="neuromodulation.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload=snap,
            )
        ]


@dataclass
class TDLearningProcess(BaseProcess):
    """Actualización TD tras ejecución motora."""

    process_id: str = "td_learning"
    period_ticks: int = 1
    priority: int = 53

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        td: TDRewardSystem = context.config.setdefault("td_system", TDRewardSystem())
        drives: DriveField | None = context.config.get("drives")
        recent = context.state_store.event_log[-10:]
        reward_ev = next((e for e in reversed(recent) if e.event_type == "reward.received"), None)
        action_ev = next((e for e in reversed(recent) if e.event_type == "action.selected"), None)
        if reward_ev is None or action_ev is None:
            return []

        prev = context.config.get("td_prev_context") or {}
        energy = context.state_store.state.homeostatic.energy
        current_drive = _top_drive(drives)
        delta = td.observe(
            prev_drive=str(prev.get("drive", current_drive)),
            prev_energy_bucket=int(prev.get("energy_bucket", _energy_bucket(energy))),
            action=str(action_ev.payload.get("action", "")),
            reward=float(reward_ev.payload.get("value", 0.0)),
            next_drive=current_drive,
            next_energy_bucket=_energy_bucket(energy),
        )
        context.config["td_prev_context"] = {
            "drive": current_drive,
            "energy_bucket": _energy_bucket(energy),
        }
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="td.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload={
                    "delta": round(delta, 5),
                    "reward": round(td.last_reward, 5),
                    "state": td.last_state,
                    "action": td.last_action,
                    "updates": td.updates,
                },
            )
        ]


@dataclass
class ConnectomePlasticityProcess(BaseProcess):
    """Plasticidad Hebbiana acotada en aristas del conectoma."""

    process_id: str = "connectome_plasticity"
    period_ticks: int = 2
    priority: int = 52
    delta_threshold: float = 0.04

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        td: TDRewardSystem | None = context.config.get("td_system")
        mods: NeuromodulatorState | None = context.config.get("modulators")
        if td is None or abs(td.last_delta) < self.delta_threshold:
            return []

        plasticity = context.router.plasticity
        scale = mods.plasticity_scale() if mods else 1.0
        delta = td.last_delta * 0.05 * scale
        changed: list[str] = []
        for source, target in PLASTIC_EDGES:
            new_w = plasticity.update(source, target, delta)
            changed.append(f"{source}->{target}:{new_w:.4f}")

        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="plasticity.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload={
                    "delta": round(td.last_delta, 5),
                    "edges_changed": len(changed),
                    "sample": changed[:3],
                },
            )
        ]
