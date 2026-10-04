"""Procesos Sprint 3 — percepción predictiva y tálamo."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.perception.active_perception import ActivePerceptionPolicy
from nexo.perception.hierarchy import PredictiveHierarchy
from nexo.perception.precision_weighting import PrecisionEstimator
from nexo.thalamus.context_gate import ContextGate
from nexo.thalamus.relay import SensoryPacket, ThalamicRelay
from nexo.thalamus.reticular import ReticularNucleus


@dataclass
class RawSensoryCaptureProcess(BaseProcess):
    """Captura sensorial cruda desde el mundo."""

    process_id: str = "raw_sensory_capture"
    period_ticks: int = 1
    priority: int = 92

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        if world is None:
            return []
        packets = [
            SensoryPacket(modality=m, embedding=tuple(float(x) for x in v), salience=s)
            for m, s, v in world.percepts_for_agent()
        ]
        context.config["raw_sensory_packets"] = packets
        return []


@dataclass
class ThalamicRelayProcess(BaseProcess):
    """Gating talámico antes de la corteza."""

    process_id: str = "thalamic_relay"
    period_ticks: int = 1
    priority: int = 88
    relay: ThalamicRelay = field(default_factory=ThalamicRelay)
    reticular: ReticularNucleus = field(default_factory=ReticularNucleus)
    context_gate: ContextGate = field(default_factory=ContextGate)

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        packets: list[SensoryPacket] = context.config.get("raw_sensory_packets") or []
        if not packets:
            return []
        state = context.state_store.state
        hctrl = context.config.get("homeostatic_controller")
        stress = hctrl.body.stress_load if hctrl else state.homeostatic.stress_load
        sleep_p = hctrl.body.sleep_pressure if hctrl else state.homeostatic.sleep_pressure
        ctx_gain = self.context_gate.compute(
            active_goals=state.active_goals,
            stress=stress,
            sleep_pressure=sleep_p,
        )
        modalities = [p.modality for p in packets]
        mask = self.reticular.mask(modalities, goals=state.active_goals)
        gated = self.relay.relay(packets, context_gain=ctx_gain, reticular_mask=mask)
        context.config["gated_sensory"] = gated
        context.router.attention_gate = ctx_gain

        tick = context.clock.tick
        t = context.clock.simulation_time
        return [
            CognitiveEvent(
                event_type="thalamus.relayed",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "modalities": [g.modality for g in gated],
                    "gains": {g.modality: g.gain for g in gated},
                    "context_gain": ctx_gain,
                },
            )
        ]


@dataclass
class PredictiveHierarchyProcess(BaseProcess):
    """Jerarquía predictiva — predicción, error, posterior."""

    process_id: str = "predictive_hierarchy"
    period_ticks: int = 1
    priority: int = 87
    hierarchy: PredictiveHierarchy = field(default_factory=PredictiveHierarchy)
    precision_estimator: PrecisionEstimator = field(default_factory=PrecisionEstimator)
    active_policy: ActivePerceptionPolicy = field(default_factory=ActivePerceptionPolicy)
    reticular: ReticularNucleus | None = None

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        gated = context.config.get("gated_sensory") or []
        if not gated:
            return []
        state = context.state_store.state
        hctrl = context.config.get("homeostatic_controller")
        stress = hctrl.body.stress_load if hctrl else 0.0
        tick = context.clock.tick
        t = context.clock.simulation_time
        events: list[CognitiveEvent] = []
        surprises: dict[str, float] = {}
        results = []

        for sig in gated:
            if sig.suppressed:
                continue
            obs = np.asarray(sig.embedding, dtype=np.float64) * sig.gain
            precision = self.precision_estimator.estimate(
                salience=sig.gain,
                modality=sig.modality,
                attention_focus=state.attention_focus,
                stress=stress,
            )
            result = self.hierarchy.update(
                modality=sig.modality,
                observation=obs,
                precision=precision,
            )
            results.append(result)
            surprises[sig.modality] = result.surprise
            if self.reticular is not None:
                self.reticular.update_habituation(sig.modality, result.surprise)

            routed = context.router.route(
                "thalamus_relay",
                f"{sig.modality}_cortex",
                np.asarray(result.posterior),
                sig.gain,
            )
            events.append(
                CognitiveEvent(
                    event_type="perception.updated",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "modality": sig.modality,
                        "embedding": tuple(float(x) for x in routed),
                        "salience": sig.gain + result.surprise * 0.3,
                        "posterior": result.posterior,
                        "prediction": result.prediction,
                    },
                )
            )
            events.append(
                CognitiveEvent(
                    event_type="perception.prediction_error",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "modality": sig.modality,
                        "error": result.error,
                        "surprise": result.surprise,
                        "precision": result.precision,
                    },
                )
            )

        context.config["prediction_results"] = results
        context.config["surprises"] = surprises
        weights = self.active_policy.resample_weights(
            [r.modality for r in results],
            surprises,
            context.rng,
        )
        context.config["active_sampling_weights"] = weights
        return events


@dataclass
class PredictiveAttentionProcess(BaseProcess):
    """Atención modulada por error de predicción (bottom-up + top-down)."""

    process_id: str = "attention"
    period_ticks: int = 2
    priority: int = 70

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        tick = context.clock.tick
        t = context.clock.simulation_time
        surprises: dict[str, float] = context.config.get("surprises") or {}
        percepts = [
            ev.payload
            for ev in context.state_store.event_log[-30:]
            if ev.event_type == "perception.updated"
        ]
        if not percepts and not surprises:
            return []

        scored: list[tuple[float, str]] = []
        goals = set(context.state_store.state.active_goals)
        seen: set[str] = set()
        for p in percepts:
            mod = str(p.get("modality", ""))
            if mod in seen:
                continue
            seen.add(mod)
            sal = float(p.get("salience", 0.0))
            pe = surprises.get(mod, 0.0)
            score = sal + pe * 0.45
            if mod == "food" and "eat" in goals:
                score += 0.2
            if mod == "danger" and ("survive" in goals or "avoid_harm" in goals):
                score += 0.35
            if mod == "distractor" and "eat" in goals:
                score -= 0.1
            scored.append((score, mod))

        for mod, pe in surprises.items():
            if mod not in seen:
                scored.append((pe * 0.5, mod))

        scored.sort(key=lambda x: -x[0])
        focus = tuple(m for _, m in scored[:2])
        return [
            CognitiveEvent(
                event_type="attention.focus_changed",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"focus": focus, "scores": {m: round(s, 4) for s, m in scored[:4]}},
            )
        ]
