"""
Circuit Hub — cableado inter-módulo basado en Brain Facts 2018.

Propaga actividad a lo largo de circuitos sensoriales, motores, límbicos,
de saliencia y homeostáticos definidos en el manifiesto del libro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .experiment_flags import get_flags

if TYPE_CHECKING:
    from .mind import InfantApeBrain

# (origen, destino, peso, etiqueta) — inspirado en Core Concepts + capítulos SfN
CIRCUIT_EDGES: tuple[tuple[str, str, float, str], ...] = (
    # Sensorial → tálamo → corteza (Ch.2)
    ("sensory", "thalamus", 0.55, "relevo sensorial"),
    ("thalamus", "sensory_cortex", 0.48, "proyección cortical"),
    ("thalamus", "amygdala", 0.22, "vía rápida emocional"),
    ("sensory_cortex", "parietal", 0.35, "integración espacial"),
    ("sensory_cortex", "hippocampus", 0.28, "codificación episódica"),
    # Motor (Ch.3)
    ("prefrontal", "basal_ganglia", 0.42, "selección Go/No-Go"),
    ("basal_ganglia", "motor", 0.5, "gate motor"),
    ("motor", "cerebellum", 0.38, "corrección motora"),
    ("cerebellum", "motor", 0.25, "feedback cerebeloso"),
    ("motor", "spinal", 0.45, "ejecución espinal"),
    # Aprendizaje / memoria / emoción (Ch.4)
    ("hippocampus", "prefrontal", 0.3, "contexto a decisión"),
    ("amygdala", "hippocampus", 0.32, "etiqueta emocional"),
    ("amygdala", "hypothalamus", 0.4, "estrés corporal"),
    ("basal_ganglia", "prefrontal", 0.2, "recompensa→plan"),
    # Pensamiento y lenguaje (Ch.5)
    ("prefrontal", "broca", 0.35, "lenguaje expresivo"),
    ("language", "prefrontal", 0.28, "comprensión→decisión"),
    ("executive", "default_mode", 0.18, "cambio de red"),
    ("default_mode", "executive", 0.15, "imaginación→foco"),
    # Saliencia (ínsula + cíngulo)
    ("insula", "salience", 0.45, "interocepción relevante"),
    ("cingulate", "salience", 0.5, "conflicto relevante"),
    ("salience", "executive", 0.38, "cambio a tarea"),
    ("salience", "amygdala", 0.25, "alerta"),
    # Cuerpo en balance (Ch.10)
    ("hypothalamus", "pituitary", 0.42, "eje hormonal"),
    ("hypothalamus", "autonomic", 0.45, "simpático/parasimpático"),
    ("vagus", "insula", 0.35, "afferencia visceral"),
    ("insula", "hypothalamus", 0.28, "homeostasis"),
    # Estados cerebrales (Ch.9)
    ("brainstem", "thalamus", 0.4, "vigilia→relevo"),
    ("brainstem", "modulators", 0.35, "monoaminas"),
    ("thalamus", "prefrontal", 0.3, "conciencia de trabajo"),
    # Plasticidad / glía
    ("glia", "synapses", 0.25, "soporte sináptico"),
    ("hippocampus", "cortex", 0.22, "consolidación"),
    # Reflejos
    ("sensory", "reflexes", 0.35, "vía rápida"),
    ("reflexes", "motor", 0.2, "respuesta refleja"),
)


@dataclass
class CircuitHub:
    last_signals: dict[str, float] = field(default_factory=dict)
    last_flows: list[dict[str, Any]] = field(default_factory=list)
    studied_boost: float = 0.0
    ticks: int = 0

    def module_signal(self, brain: InfantApeBrain, module_id: str) -> float:
        c = brain.cortex
        hippo_act = 0.0
        if hasattr(brain, "hippo"):
            v_dg = float(brain.hippo.dg.v.mean()) if brain.hippo.dg.v.size else 0
            hippo_act = float(np.clip((v_dg + 70) / 25, 0, 1))

        mapping: dict[str, float] = {
            "sensory": float(np.clip(c.sensory.v.mean() if c.sensory.v.size else 0, 0, 1) or 0.3),
            "sensory_cortex": float(np.clip(c.sensory.v.mean() * 0.9 if c.sensory.v.size else 0, 0, 1)),
            "thalamus": float(brain.modulators.acetylcholine * 0.5 + brain.modulators.glutamate_drive * 0.4),
            "prefrontal": float(np.clip((c.prefrontal.v.mean() + 70) / 30 if c.prefrontal.v.size else 0, 0, 1)),
            "motor": float(np.clip(c.motor.spikes.mean() * 2 if c.motor.spikes.size else 0, 0, 1)),
            "limbic": float(np.clip(c.limbic.v.mean() if c.limbic.v.size else 0, 0, 1)),
            "cortex": float(np.clip(c.associative.v.mean() if c.associative.v.size else 0, 0, 1)),
            "hippocampus": hippo_act,
            "amygdala": float(np.clip(abs(brain.amygdala.valence) * 0.5 + brain.amygdala.arousal * 0.5, 0, 1)),
            "hypothalamus": float(np.clip(brain.hypothalamus.energy * 0.5 + (1 - brain.hypothalamus.cortisol) * 0.3, 0, 1)),
            "basal_ganglia": float(np.clip(brain.modulators.dopamine * 0.6 + brain.basal_ganglia.habit.mean() * 0.15, 0, 1)),
            "cerebellum": float(np.clip(len(brain.cerebellum.buffer) / 8.0, 0, 1)),
            "broca": float(np.clip(brain.modulators.dopamine * 0.35 + brain.persona.energy * 0.35, 0, 1)),
            "language": 0.7 if brain.language.available else 0.35,
            "brainstem": float(np.clip(1.0 - brain.brainstem.sleep_pressure, 0, 1)),
            "insula": brain.insula.interoceptive_salience,
            "cingulate": brain.cingulate.conflict_level,
            "salience": float(np.clip(brain.cingulate.conflict_level * 0.5 + brain.insula.interoceptive_salience * 0.5, 0, 1)),
            "executive": float(np.clip(brain.modulators.acetylcholine * 0.5 + brain.deliberation.last.agency * 0.4, 0, 1)),
            "default_mode": float(
                np.clip(
                    0.2
                    + (0.4 if (brain.imagination.last or {}).get("active") else 0),
                    0,
                    1,
                )
            ),
            "parietal": float(
                np.clip(brain.atlas.parietal.body_schema * brain.atlas.parietal.spatial_coherence, 0, 1)
            ),
            "pituitary": float(np.clip(brain.hypothalamus.cortisol * 0.55, 0, 1)),
            "autonomic": float(np.clip(brain.hypothalamus.cortisol * 0.4 + brain.modulators.norepinephrine * 0.35, 0, 1)),
            "vagus": float(np.clip(brain.body.comfort * 0.5, 0, 1)),
            "spinal": float(np.clip(brain.body.total_pain() * 0.5 + brain.reflexes.startle * 0.35, 0, 1)),
            "glia": brain.atlas.glia.astrocyte_tone,
            "synapses": float(np.clip(sum(float(np.abs(s.w).mean()) for s in c.iter_synapses()) / 0.35, 0, 1)),
            "modulators": float(np.clip(brain.modulators.dopamine + brain.modulators.serotonin, 0, 1) / 2),
            "reflexes": float(np.clip(brain.reflexes.startle, 0, 1)),
        }
        base = mapping.get(module_id, 0.15)
        if brain.brain_facts.focus_modules and module_id in brain.brain_facts.focus_modules:
            base = float(np.clip(base + 0.18 + self.studied_boost * 0.1, 0, 1))
        return base

    def tick(
        self,
        brain: InfantApeBrain,
        *,
        vision: dict | None = None,
        ambient: dict | None = None,
        surprise: float = 0.0,
    ) -> dict[str, Any]:
        self.ticks += 1
        if get_flags(brain).enable_multimodal_delays:
            brain.sensory_hub.use_delays = True
        brain.sensory_hub.route(brain, vision)
        insula = brain.insula.integrate(brain)
        cing = brain.cingulate.integrate(brain, surprise=surprise)
        states = brain.brain_states.integrate(brain, ambient)

        signals: dict[str, float] = {}
        for src, dst, weight, label in CIRCUIT_EDGES:
            if src not in signals:
                signals[src] = self.module_signal(brain, src)
            if dst not in signals:
                signals[dst] = self.module_signal(brain, dst)

        flows: list[dict[str, Any]] = []
        for src, dst, weight, label in CIRCUIT_EDGES:
            flow = signals[src] * weight
            signals[dst] = float(np.clip(signals[dst] + flow * 0.12, 0, 1))
            if flow > 0.08:
                flows.append({"from": src, "to": dst, "flow": round(flow, 3), "label": label})
                brain.signal_bus.emit(src, dst, flow, label=label)

        delivered = brain.signal_bus.tick(dt_ms=2.0)
        brain.signal_bus.apply_delivered(brain, delivered)

        if get_flags(brain).enable_regional_lobe_bus:
            from .regional_latency import LOBE_WHITE_MATTER_CHAIN

            lobes = (brain.lobes.last or {}).get("vectors") or {}
            for src, dst in LOBE_WHITE_MATTER_CHAIN:
                strength = float(np.clip(np.mean(np.abs(lobes.get(src, [0.0]))) * 0.35, 0, 1))
                if strength > 0.06:
                    brain.signal_bus.emit(src, dst, strength, label="lobe_wm")

        self._apply_effects(brain, signals)
        self.last_signals = {k: round(v, 3) for k, v in signals.items()}
        self.last_flows = sorted(flows, key=lambda f: f["flow"], reverse=True)[:12]

        return {
            "signals": self.last_signals,
            "top_flows": self.last_flows,
            "insula": insula,
            "cingulate": cing,
            "brain_state": states,
            "sensory": brain.sensory_hub.last_modalities,
        }

    def _apply_effects(self, brain: InfantApeBrain, signals: dict[str, float]) -> None:
        sg = signals.get
        dop = 0.02 * sg("basal_ganglia", 0) + 0.015 * sg("salience", 0)
        brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + dop, 0, 1))
        ach = 0.02 * sg("thalamus", 0) + 0.015 * sg("executive", 0)
        brain.modulators.acetylcholine = float(np.clip(brain.modulators.acetylcholine + ach, 0, 1))
        ne = 0.025 * sg("amygdala", 0) + 0.02 * sg("cingulate", 0)
        brain.modulators.norepinephrine = float(np.clip(brain.modulators.norepinephrine + ne, 0, 1))

        motor_bias = 0.08 * sg("motor", 0) + 0.06 * sg("cerebellum", 0)
        if motor_bias > 0.05 and brain.cortex.motor.v.size:
            brain.cortex.motor.v += motor_bias * 0.5

        hippo_boost = 0.06 * sg("hippocampus", 0)
        if hippo_boost > 0.03:
            brain.hippocampus.encoding_gain = float(
                np.clip(getattr(brain.hippocampus, "encoding_gain", 1.0) + hippo_boost * 0.1, 0.8, 1.4)
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticks": self.ticks,
            "studied_boost": round(self.studied_boost, 3),
            "top_flows": self.last_flows[:8],
            "active_modules": sorted(
                [(k, v) for k, v in self.last_signals.items() if v > 0.35],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }
