"""
Atlas neuroanatómico — estructuras reales mapeadas a módulos de Nexo.

Hemisferios + cuerpo calloso, lóbulos, límbico, tronco, cerebelo, glía, ventrículos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .curriculum import anatomy_focus_boost

# Definiciones estáticas (contenido educativo ↔ código)
STRUCTURES: tuple[dict[str, Any], ...] = (
    {
        "id": "hemisphere_left",
        "group": "hemispheres",
        "name": "Hemisferio izquierdo",
        "role": "Lenguaje, análisis, secuencia, Broca/Wernicke",
        "note": "Ambos hemisferios cooperan; no existe «solo izquierdo».",
    },
    {
        "id": "hemisphere_right",
        "group": "hemispheres",
        "name": "Hemisferio derecho",
        "role": "Espacio, rostros, emoción, visión global, creatividad",
        "note": "Integrado con el izquierdo vía cuerpo calloso.",
    },
    {
        "id": "corpus_callosum",
        "group": "hemispheres",
        "name": "Cuerpo calloso",
        "role": "Puente de fibras entre hemisferios",
        "note": "Mezcla actividad asociativa izquierda/derecha cada tick.",
    },
    {
        "id": "lobe_frontal",
        "group": "lobes",
        "name": "Lóbulo frontal",
        "role": "Decisiones, planificación, impulsos, personalidad, movimiento voluntario",
        "module": "prefrontal",
    },
    {
        "id": "lobe_parietal",
        "group": "lobes",
        "name": "Lóbulo parietal",
        "role": "Tacto, cuerpo en el espacio, orientación, vista↔movimiento",
        "module": "parietal",
    },
    {
        "id": "lobe_temporal",
        "group": "lobes",
        "name": "Lóbulo temporal",
        "role": "Audición, memoria, lenguaje comprensivo, rostros, emoción",
        "module": "limbic",
    },
    {
        "id": "lobe_occipital",
        "group": "lobes",
        "name": "Lóbulo occipital",
        "role": "Visión — formas, color, movimiento, profundidad",
        "module": "sensory",
    },
    {
        "id": "cerebellum",
        "group": "subcortex",
        "name": "Cerebelo",
        "role": "Equilibrio, coordinación, automatización motora",
        "module": "cerebellum",
    },
    {
        "id": "brainstem_midbrain",
        "group": "brainstem",
        "name": "Mesencéfalo",
        "role": "Reflejos visuales/auditivos, alerta, movimiento ocular",
    },
    {
        "id": "brainstem_pons",
        "group": "brainstem",
        "name": "Puente (protuberancia)",
        "role": "Sueño, respiración, enlace cerebro–cerebelo",
        "module": "brainstem",
    },
    {
        "id": "brainstem_medulla",
        "group": "brainstem",
        "name": "Bulbo raquídeo",
        "role": "Respiración, ritmo cardíaco, reflejos vitales automáticos",
    },
    {
        "id": "thalamus",
        "group": "limbic",
        "name": "Tálamo",
        "role": "Relevo y filtro sensorial hacia la corteza",
        "module": "thalamus",
    },
    {
        "id": "hypothalamus",
        "group": "limbic",
        "name": "Hipotálamo",
        "role": "Hambre, sed, sueño, temperatura, hormonas, estrés",
        "module": "hypothalamus",
    },
    {
        "id": "amygdala",
        "group": "limbic",
        "name": "Amígdala",
        "role": "Miedo, amenaza, memoria emocional, alerta",
        "module": "amygdala",
    },
    {
        "id": "hippocampus",
        "group": "limbic",
        "name": "Hipocampo",
        "role": "Memoria episódica, contexto, lugar y tiempo",
        "module": "hippocampus",
    },
    {
        "id": "basal_ganglia",
        "group": "subcortex",
        "name": "Ganglios basales",
        "role": "Go/No-Go motor, hábitos, recompensa",
        "module": "basal_ganglia",
    },
    {
        "id": "broca",
        "group": "language",
        "name": "Área de Broca",
        "role": "Lenguaje expresivo / producción",
        "module": "broca",
    },
    {
        "id": "wernicke",
        "group": "language",
        "name": "Área de Wernicke",
        "role": "Comprensión del lenguaje",
        "module": "language",
    },
    {
        "id": "gray_matter",
        "group": "tissue",
        "name": "Sustancia gris",
        "role": "Cuerpos neuronales — procesamiento local",
    },
    {
        "id": "white_matter",
        "group": "tissue",
        "name": "Sustancia blanca",
        "role": "Axones mielinizados — conexión entre regiones",
        "module": "synapses",
    },
    {
        "id": "glia",
        "group": "support",
        "name": "Células gliales",
        "role": "Astrocitos, oligodendrocitos, microglía, epéndimo",
        "module": "glia",
    },
    {
        "id": "ventricles",
        "group": "support",
        "name": "Ventrículos / LCR",
        "role": "Protección, nutrientes, eliminación de desechos",
        "module": "ventricles",
    },
    {
        "id": "meninges",
        "group": "support",
        "name": "Meninges",
        "role": "Protección en tres capas (duramadre, aracnoides, piamadre)",
    },
    {
        "id": "blood_supply",
        "group": "support",
        "name": "Irrigación cerebral",
        "role": "Oxígeno y glucosa — polígono de Willis",
        "module": "perfusion",
    },
    {
        "id": "insula",
        "group": "limbic",
        "name": "Ínsula",
        "role": "Interocepción, emoción visceral, empatía, náusea",
        "module": "insula",
    },
    {
        "id": "cingulate",
        "group": "limbic",
        "name": "Cíngulo",
        "role": "Conflicto, error, dolor emocional, motivación",
        "module": "cingulate",
    },
    {
        "id": "pituitary",
        "group": "limbic",
        "name": "Hipófisis",
        "role": "Puente hormonal — eje HPA, tiroides, crecimiento",
        "module": "pituitary",
    },
    {
        "id": "spinal_cord",
        "group": "peripheral",
        "name": "Médula espinal",
        "role": "Vías ascendentes/descendentes y reflejos",
        "module": "spinal",
    },
    {
        "id": "dorsal_horn",
        "group": "peripheral",
        "name": "Asta dorsal (laminas I–II)",
        "role": "Relé nociceptivo — fibras Aδ y C, wide dynamic range",
        "module": "nociception",
    },
    {
        "id": "peripheral_nociceptor",
        "group": "peripheral",
        "name": "Terminales nociceptivos periféricos",
        "role": "Transducción mecánica/térmica/química en extremidades y víscera",
        "module": "nociception",
    },
    {
        "id": "a_delta_fiber",
        "group": "peripheral",
        "name": "Fibras Aδ",
        "role": "Dolor rápido, punzante, bien localizado",
        "module": "nociception",
    },
    {
        "id": "c_fiber",
        "group": "peripheral",
        "name": "Fibras C",
        "role": "Dolor lento, difuso, quemante y visceral",
        "module": "nociception",
    },
    {
        "id": "thalamus_vpm",
        "group": "subcortex",
        "name": "Tálamo (VPM/VPL)",
        "role": "Relé nociceptivo al córtex somatosensitivo e ínsula",
        "module": "nociception",
    },
    {
        "id": "locomotor_apparatus",
        "group": "body",
        "name": "Aparato locomotor",
        "role": "Huesos, articulaciones y músculos — movimiento y postura",
        "module": "locomotor",
    },
    {
        "id": "osteology",
        "group": "body",
        "name": "Osteología",
        "role": "Esqueleto axial y apendicular — soporte y palancas",
        "module": "osteology",
    },
    {
        "id": "arthrology",
        "group": "body",
        "name": "Artrología",
        "role": "Articulaciones sinoviales, fibrosas y cartilaginosas",
        "module": "arthrology",
    },
    {
        "id": "myology",
        "group": "body",
        "name": "Miología",
        "role": "Músculos esqueléticos — origen, inserción, acción",
        "module": "myology",
    },
    {
        "id": "brachial_plexus",
        "group": "body",
        "name": "Plexo braquial",
        "role": "Inervación motora y sensitiva del miembro superior",
        "module": "brachial_plexus",
    },
    {
        "id": "lumbosacral_plexus",
        "group": "body",
        "name": "Plexo lumbosacro",
        "role": "Inervación del miembro inferior — ciático, femoral",
        "module": "lumbosacral",
    },
    {
        "id": "autonomic",
        "group": "peripheral",
        "name": "Sistema autónomo",
        "role": "Simpático / parasimpático — corazón, digestión, estrés",
        "module": "autonomic",
    },
    {
        "id": "vagus",
        "group": "peripheral",
        "name": "Nervio vago",
        "role": "Comunicación cuerpo↔cerebro, calma y digestión",
        "module": "vagus",
    },
    {
        "id": "network_default",
        "group": "networks",
        "name": "Red por defecto",
        "role": "Yo, recuerdos, imaginación, narrativa personal",
        "module": "default_mode",
    },
    {
        "id": "network_executive",
        "group": "networks",
        "name": "Red ejecutiva",
        "role": "Foco, planificación, memoria de trabajo",
        "module": "executive",
    },
    {
        "id": "network_salience",
        "group": "networks",
        "name": "Red de saliencia",
        "role": "Detecta importancia — ínsula + cíngulo anterior",
        "module": "salience",
    },
)

NEUROTRANSMITTERS: tuple[dict[str, str], ...] = (
    {"id": "dopamine", "name": "Dopamina", "role": "Motivación, recompensa, movimiento, aprendizaje"},
    {"id": "serotonin", "name": "Serotonina", "role": "Ánimo, sueño, impulsividad"},
    {"id": "norepinephrine", "name": "Noradrenalina", "role": "Alerta, estrés, atención"},
    {"id": "gaba", "name": "GABA", "role": "Freno inhibitorio, calma"},
    {"id": "glutamate", "name": "Glutamato", "role": "Excitación principal, aprendizaje"},
    {"id": "acetylcholine", "name": "Acetilcolina", "role": "Atención, memoria, movimiento"},
    {"id": "oxytocin", "name": "Oxitocina", "role": "Vínculo social, confianza"},
    {"id": "cortisol", "name": "Cortisol", "role": "Estrés prolongado, eje HPA"},
)


def _pop_activity(pop) -> float:
    if pop is None or not hasattr(pop, "v"):
        return 0.0
    denom = max(getattr(pop, "v_thresh", -52) - getattr(pop, "v_rest", -70), 1.0)
    act = np.clip((pop.v - pop.v_rest) / denom, 0, 1.25)
    if hasattr(pop, "spikes") and pop.spikes.any():
        act = np.maximum(act, pop.spikes.astype(np.float32))
    return float(np.clip(act.mean(), 0, 1))


@dataclass
class CorpusCallosum:
    """Puente interhemisférico — mezcla mitades de la corteza asociativa."""

    last_transfer: float = 0.0
    asymmetry: float = 0.0
    gamma_sync: float = 0.0

    def integrate(self, brain) -> dict[str, float]:
        from .experiment_flags import get_flags

        assoc = brain.cortex.associative
        n = assoc.n
        if n < 4:
            return {"transfer": 0.0, "asymmetry": 0.0, "gamma_sync": 0.0}
        mid = n // 2
        left = assoc.v[:mid].astype(np.float32).copy()
        right = assoc.v[mid:].astype(np.float32).copy()
        self.asymmetry = float(abs(left.mean() - right.mean()))
        mix = 0.12 + 0.08 * (1.0 - brain.modulators.gaba_tone)
        self.gamma_sync = 0.0
        if get_flags(brain).enable_rhythm_pac:
            snap = brain.oscillators.last_snapshot
            if snap:
                phase_coherence = 0.5 + 0.5 * np.cos(brain.oscillators.gamma_phase)
                self.gamma_sync = float(phase_coherence * snap.pac_coupling)
                mix = float(np.clip(mix * (0.82 + 0.35 * self.gamma_sync), 0.05, 0.35))
        assoc.v[:mid] = np.clip(left * (1 - mix) + right.mean() * mix, assoc.v_rest, 40)
        assoc.v[mid:] = np.clip(right * (1 - mix) + left.mean() * mix, assoc.v_rest, 40)
        self.last_transfer = mix
        return {
            "transfer": round(mix, 3),
            "asymmetry": round(self.asymmetry, 3),
            "gamma_sync": round(self.gamma_sync, 3),
        }


@dataclass
class ParietalIntegrator:
    """Lóbulo parietal — esquema corporal + espacio (propriocepción simulada)."""

    body_schema: float = 0.5
    spatial_coherence: float = 0.5

    def integrate(self, brain) -> dict[str, float]:
        body = brain.body
        pain = body.total_pain()
        comfort = body.comfort
        agent_x, agent_y = brain.world.agent_x, brain.world.agent_y
        room = brain.world.current_room()
        vision = brain._last_vision or {}
        fix = vision.get("fixation") or {}
        dist = float(fix.get("distance", 999)) if fix else 999.0

        self.body_schema = float(np.clip(0.55 * comfort + 0.25 * (1 - pain) + 0.2, 0, 1))
        self.spatial_coherence = float(
            np.clip(0.4 + (0.35 if dist < 80 else 0.1) + (0.15 if room != "jardín" else 0.05), 0, 1)
        )
        return {
            "body_schema": round(self.body_schema, 3),
            "spatial_coherence": round(self.spatial_coherence, 3),
            "hand_eye": round(min(1.0, self.body_schema * self.spatial_coherence), 3),
        }


@dataclass
class GliaSupport:
    """Metabolismo glial — modula ganancia, tripartita sináptica y neuroinflamación."""

    astrocyte_tone: float = 0.55
    microglia_load: float = 0.1
    myelin_efficiency: float = 0.72
    glycogen_reserve: float = 0.62
    tripartite_gain: float = 0.48

    def step(self, brain) -> dict[str, float]:
        pain = brain.body.total_pain()
        sleep = brain.brainstem.sleep_pressure
        cortisol = brain.hypothalamus.cortisol
        activity = float(brain.cortex.associative.spikes.mean())

        inflammation = pain * 0.25 + cortisol * 0.08 + activity * 0.05
        self.microglia_load = float(np.clip(self.microglia_load * 0.9 + inflammation, 0, 1))
        self.astrocyte_tone = float(
            np.clip(0.7 * self.astrocyte_tone + 0.3 * (0.5 + brain.body.comfort * 0.4), 0.3, 1)
        )
        self.glycogen_reserve = float(
            np.clip(
                self.glycogen_reserve * 0.995
                + (1 - float(getattr(brain.body, "hunger", 0))) * 0.012
                - activity * 0.018
                + (0.015 if sleep > 0.55 else 0.0),
                0.15,
                1.0,
            )
        )
        self.tripartite_gain = float(np.clip(0.35 + 0.45 * self.astrocyte_tone - 0.25 * self.microglia_load, 0.1, 0.85))
        self.myelin_efficiency = float(np.clip(0.85 * self.myelin_efficiency + 0.15 * (1 - sleep * 0.4), 0.4, 1))

        gain_bump = (
            0.02 * self.astrocyte_tone
            + 0.015 * self.tripartite_gain
            + 0.01 * self.glycogen_reserve
            - 0.04 * self.microglia_load
        )
        plasticity_damp = 1.0 - 0.12 * self.microglia_load
        brain.cortex.plasticity_mult = float(
            np.clip(brain.profile.plasticity_mult * plasticity_damp, brain.profile.plasticity_mult * 0.75, brain.profile.plasticity_mult * 1.05)
        )
        current_gain = float(brain.cortex.synaptic_gain)
        brain.cortex.synaptic_gain = float(
            np.clip(current_gain * (1 + gain_bump), brain.profile.synaptic_gain * 0.85, brain.profile.synaptic_gain * 1.18)
        )
        return {
            "astrocyte": round(self.astrocyte_tone, 3),
            "microglia": round(self.microglia_load, 3),
            "myelin": round(self.myelin_efficiency, 3),
            "glycogen": round(self.glycogen_reserve, 3),
            "tripartite": round(self.tripartite_gain, 3),
        }


@dataclass
class VentricleCSF:
    """Líquido cefalorraquídeo — carga metabólica / sueño."""

    pressure: float = 0.35
    clearance: float = 0.5

    def step(self, brain) -> dict[str, float]:
        sleep = brain.brainstem.sleep_pressure
        activity = _pop_activity(brain.cortex.associative)
        self.pressure = float(np.clip(0.6 * self.pressure + 0.4 * (0.25 + activity * 0.5), 0.1, 1))
        if sleep > 0.55:
            self.clearance = float(np.clip(self.clearance + 0.08, 0, 1))
            brain.brainstem.rest(0.02)
        else:
            self.clearance = float(np.clip(self.clearance * 0.98, 0.2, 1))
        return {"pressure": round(self.pressure, 3), "clearance": round(self.clearance, 3)}


@dataclass
class BrainstemNuclei:
    """Tronco encefálico extendido — mesencéfalo, puente, bulbo."""

    midbrain_alert: float = 0.4
    pons_sleep: float = 0.3
    medulla_vitals: float = 0.85

    def step(self, brain, *, surprise: float = 0.0) -> dict[str, float]:
        self.midbrain_alert = float(
            np.clip(0.5 * self.midbrain_alert + 0.5 * (brain.amygdala.arousal + surprise * 0.4), 0, 1)
        )
        self.pons_sleep = float(np.clip(brain.brainstem.sleep_pressure, 0, 1))
        comfort = brain.body.comfort
        pain = brain.body.total_pain()
        self.medulla_vitals = float(np.clip(0.7 * comfort + 0.3 * (1 - pain), 0.2, 1))
        return {
            "midbrain": round(self.midbrain_alert, 3),
            "pons": round(self.pons_sleep, 3),
            "medulla": round(self.medulla_vitals, 3),
        }


@dataclass
class BrainAtlas:
    """Orquesta todas las estructuras y exporta actividad en tiempo real."""

    corpus: CorpusCallosum = field(default_factory=CorpusCallosum)
    parietal: ParietalIntegrator = field(default_factory=ParietalIntegrator)
    glia: GliaSupport = field(default_factory=GliaSupport)
    ventricles: VentricleCSF = field(default_factory=VentricleCSF)
    brainstem: BrainstemNuclei = field(default_factory=BrainstemNuclei)
    last: dict = field(default_factory=dict)

    def prepare_episode(self, brain) -> None:
        """Antes de simular spikes — puente interhemisférico y soporte glial."""
        self.corpus.integrate(brain)
        if getattr(brain, "vascular", None) is not None:
            brain.vascular.step(brain)
        self.glia.step(brain)

    def update(self, brain, *, surprise: float = 0.0) -> dict[str, Any]:
        c = brain.cortex
        pfc_act = _pop_activity(c.prefrontal)
        assoc_act = _pop_activity(c.associative)
        conflict = 0.2
        if brain.cognition.last_summary:
            conflict = float(brain.cognition.last_summary.get("conflict", 0.2))
        imag_active = bool(getattr(brain.imagination, "last", {}) and brain.imagination.last.get("active"))
        activities: dict[str, float] = {
            "sensory": _pop_activity(c.sensory),
            "limbic": _pop_activity(c.limbic),
            "associative": assoc_act,
            "prefrontal": pfc_act,
            "motor": _pop_activity(c.motor),
            "hippocampus": float(
                np.clip(
                    (_pop_activity(brain.hippo.dg) + _pop_activity(brain.hippo.ca3) + _pop_activity(brain.hippo.ca1)) / 3,
                    0,
                    1,
                )
            ),
            "amygdala": float(np.clip(abs(brain.amygdala.valence) * 0.5 + brain.amygdala.arousal * 0.5, 0, 1)),
            "hypothalamus": float(np.clip(brain.hypothalamus.energy * 0.4 + (1 - brain.hypothalamus.cortisol) * 0.3, 0, 1)),
            "thalamus": float(np.clip(brain.modulators.acetylcholine * 0.6 + brain.modulators.glutamate_drive * 0.4, 0, 1)),
            "basal_ganglia": float(np.clip(brain.modulators.dopamine * 0.55 + brain.basal_ganglia.habit.mean() * 0.15, 0, 1)),
            "cerebellum": float(np.clip(len(brain.cerebellum.buffer) / 8.0, 0, 1)),
            "broca": float(np.clip(brain.modulators.dopamine * 0.3 + brain.persona.energy * 0.4, 0, 1)),
            "language": 0.65 if brain.language.available else 0.35,
            "hemisphere_left": _pop_activity(c.associative) * 0.95,
            "hemisphere_right": _pop_activity(c.associative) * (0.95 + self.corpus.asymmetry * 0.1),
            "corpus_callosum": self.corpus.last_transfer,
            "synapses": float(
                np.clip(sum(float(np.abs(s.w).mean()) for s in c.iter_synapses()) / 0.35, 0, 1)
            ),
            "glia": self.glia.astrocyte_tone,
            "ventricles": self.ventricles.pressure,
            "perfusion": float(np.clip(0.55 + brain.body.comfort * 0.35 - brain.body.total_pain() * 0.2, 0.2, 1)),
            "insula": float(np.clip((1 - brain.body.comfort) * 0.45 + brain.body.total_pain() * 0.35 + abs(brain.amygdala.valence) * 0.2, 0, 1)),
            "cingulate": float(np.clip(conflict + surprise * 0.35, 0, 1)),
            "pituitary": float(np.clip(brain.hypothalamus.cortisol * 0.55 + (1 - brain.hypothalamus.energy) * 0.25, 0, 1)),
            "spinal": float(np.clip(brain.body.total_pain() * 0.55 + brain.reflexes.startle * 0.35, 0, 1)),
            "nociception": float(np.clip(
                brain.nociceptor.total() if hasattr(brain, "nociceptor") else brain.body.total_pain() * 0.65,
                0,
                1,
            )),
            "locomotor": float(np.clip(
                0.28 + brain.body.pain_limbs * 0.25 + (1 - brain.body.comfort) * 0.15,
                0,
                1,
            )),
            "osteology": 0.42,
            "arthrology": 0.38,
            "myology": 0.4,
            "brachial_plexus": 0.35,
            "lumbosacral": 0.35,
            "autonomic": float(np.clip(brain.hypothalamus.cortisol * 0.4 + brain.modulators.norepinephrine * 0.35, 0, 1)),
            "vagus": float(np.clip(brain.body.comfort * 0.5 + (1 - brain.hypothalamus.cortisol) * 0.3, 0, 1)),
            "default_mode": float(np.clip((0.45 if imag_active else 0.15) + assoc_act * 0.35, 0, 1)),
            "executive": float(np.clip(pfc_act * 0.65 + brain.modulators.acetylcholine * 0.35, 0, 1)),
            "salience": float(np.clip(abs(brain.amygdala.valence) * 0.4 + surprise * 0.45, 0, 1)),
        }

        par = self.parietal.integrate(brain)
        activities["parietal"] = par["hand_eye"]

        stem = self.brainstem.step(brain, surprise=surprise)
        vent = self.ventricles.step(brain)
        glia = {"astrocyte": self.glia.astrocyte_tone, "microglia": self.glia.microglia_load, "myelin": self.glia.myelin_efficiency}

        focus: list[str] = []
        if hasattr(brain, "curriculum"):
            brain.curriculum.tick_focus()
            focus = list(brain.curriculum.focus_anatomy)
        if hasattr(brain, "anatomy"):
            focus.extend(brain.anatomy.focus_anatomy)

        structures = []
        for sdef in STRUCTURES:
            sid = sdef["id"]
            mod = sdef.get("module")
            activity = activities.get(mod or sid, 0.0)
            if sid == "lobe_frontal":
                activity = activities["prefrontal"]
            elif sid == "lobe_occipital":
                activity = activities["sensory"] * 0.85
            elif sid == "lobe_temporal":
                activity = (activities["limbic"] + activities["hippocampus"]) / 2
            elif sid == "lobe_parietal":
                activity = activities["parietal"]
            elif sid == "brainstem_midbrain":
                activity = stem["midbrain"]
            elif sid == "brainstem_pons":
                activity = stem["pons"]
            elif sid == "brainstem_medulla":
                activity = stem["medulla"]
            elif sid == "gray_matter":
                activity = float(np.mean([activities["associative"], activities["limbic"], activities["prefrontal"]]))
            elif sid == "white_matter":
                activity = activities["synapses"]
            elif sid == "wernicke":
                activity = activities["language"]
            elif sid == "meninges":
                activity = 0.25
            elif sid == "blood_supply":
                activity = activities["perfusion"]
            elif sid == "insula":
                activity = activities["insula"]
            elif sid == "cingulate":
                activity = activities["cingulate"]
            elif sid == "pituitary":
                activity = activities["pituitary"]
            elif sid == "spinal_cord":
                activity = activities["spinal"]
            elif sid in ("dorsal_horn", "peripheral_nociceptor", "a_delta_fiber", "c_fiber", "thalamus_vpm"):
                activity = activities["nociception"]
            elif sid == "locomotor_apparatus":
                activity = activities["locomotor"]
            elif sid == "osteology":
                activity = activities["osteology"]
            elif sid == "arthrology":
                activity = activities["arthrology"]
            elif sid == "myology":
                activity = activities["myology"]
            elif sid == "brachial_plexus":
                activity = activities["brachial_plexus"]
            elif sid == "lumbosacral_plexus":
                activity = activities["lumbosacral"]
            elif sid == "autonomic":
                activity = activities["autonomic"]
            elif sid == "vagus":
                activity = activities["vagus"]
            elif sid == "network_default":
                activity = activities["default_mode"]
            elif sid == "network_executive":
                activity = activities["executive"]
            elif sid == "network_salience":
                activity = activities["salience"]
            activity = anatomy_focus_boost(sid, activity, focus)
            structures.append(
                {
                    **{k: v for k, v in sdef.items() if k != "module"},
                    "activity": round(float(np.clip(activity, 0, 1)), 3),
                }
            )

        transmitters = []
        mods = brain.modulators.to_dict()
        aff = brain.affect.to_dict() if hasattr(brain, "affect") else {}
        pools = aff.get("pools", {})
        for nt in NEUROTRANSMITTERS:
            key = nt["id"]
            if key == "gaba":
                val = mods.get("gaba_tone", 0.4)
            elif key == "glutamate":
                val = mods.get("glutamate_drive", 0.5)
            elif key == "cortisol":
                val = brain.hypothalamus.cortisol
            elif key in pools:
                val = pools[key].get("bound", mods.get(key, 0.5))
            else:
                val = mods.get(key, 0.5)
            transmitters.append({**nt, "level": round(float(val), 3)})

        orchestra = self._orchestrate(brain, activities, stem, surprise)

        self.last = {
            "structures": structures,
            "transmitters": transmitters,
            "hemispheres": {
                "left": round(activities["hemisphere_left"], 3),
                "right": round(activities["hemisphere_right"], 3),
                "corpus_callosum": self.corpus.last_transfer,
                "asymmetry": round(self.corpus.asymmetry, 3),
            },
            "parietal": par,
            "brainstem": stem,
            "glia": glia,
            "ventricles": vent,
            "perfusion": round(activities["perfusion"], 3),
            "orchestra": orchestra,
            "groups": self._group_summary(structures),
        }
        return self.last

    def _group_summary(self, structures: list[dict]) -> dict[str, float]:
        groups: dict[str, list[float]] = {}
        for s in structures:
            g = s.get("group", "other")
            groups.setdefault(g, []).append(s.get("activity", 0))
        return {g: round(float(np.mean(v)), 3) for g, v in groups.items()}

    def _orchestrate(self, brain, activities: dict, stem: dict, surprise: float) -> list[str]:
        """Narrativa de «un día normal» según qué estructuras están activas."""
        lines: list[str] = []
        if stem["medulla"] > 0.5:
            lines.append("Bulbo raquídeo mantiene respiración y ritmo vital.")
        if brain.hypothalamus.cortisol > 0.4 or brain.body.hunger > 0.35:
            lines.append("Hipotálamo regula hambre, sed o estrés hormonal.")
        if activities["thalamus"] > 0.35:
            lines.append("Tálamo filtra estímulos hacia la corteza.")
        if activities["sensory"] > 0.25:
            lines.append("Occipital y vías visuales procesan el entorno.")
        if activities["limbic"] > 0.3 or activities["amygdala"] > 0.35:
            lines.append("Temporal y amígdala evalúan sonido, memoria y emoción.")
        if activities["hippocampus"] > 0.2:
            lines.append("Hipocampo consolida recuerdos y contexto.")
        if activities["prefrontal"] > 0.25:
            lines.append("Frontal y prefrontal planifican y frenan impulsos.")
        if activities["parietal"] > 0.35:
            lines.append("Parietal ubica el cuerpo en el espacio.")
        if activities["cerebellum"] > 0.2:
            lines.append("Cerebelo suaviza y automatiza movimientos.")
        if activities["basal_ganglia"] > 0.3:
            lines.append("Ganglios basales seleccionan hábitos y acciones.")
        if surprise > 0.45:
            lines.append("Mesencéfalo eleva alerta ante lo inesperado.")
        if hasattr(brain, "curriculum") and brain.curriculum.focus_ticks > 0 and brain.curriculum.last_key:
            sec = brain.curriculum.last_key
            lines.append(f"Estudiando currículo: {sec.replace('_', ' ')} — estructuras relacionadas activas.")
        if hasattr(brain, "temporal") and brain.temporal.last_observe:
            lines.append(f"Ritmo temporal: {brain.temporal.last_observe.get('felt', '—')}.")
        if not lines:
            lines.append("Red en reposo — funciones vitales de fondo.")
        return lines[:8]

    def to_dict(self) -> dict:
        return dict(self.last) if self.last else {}
