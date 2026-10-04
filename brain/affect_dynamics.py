"""
Dinámica afectiva y social — Bloque G (items 67–76).

HPA, regulación PFC→amígdala, empatía, apego, vergüenza, liking/wanting,
frustración, ánimo persistente y turnos sociales.
Nunca escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .experiment_flags import get_flags

ATTACHMENT_SECURE = "secure"
ATTACHMENT_ANXIOUS = "anxious"
ATTACHMENT_AVOIDANT = "avoidant"


@dataclass
class HPAAxis:
    """Eje CRH → ACTH → cortisol (item 68)."""

    crh: float = 0.18
    acth: float = 0.16
    pulses: int = 0

    def step(self, brain, *, stress: float) -> dict[str, float]:
        s = float(np.clip(stress, 0, 1))
        self.crh = float(np.clip(0.86 * self.crh + 0.14 * s, 0, 1))
        self.acth = float(np.clip(0.88 * self.acth + 0.12 * self.crh, 0, 1))
        cort_release = 0.015 + 0.11 * self.acth
        brain.affect.cortisol.release(cort_release)
        brain.hypothalamus.cortisol = float(
            np.clip(0.62 * brain.hypothalamus.cortisol + 0.38 * brain.affect.cortisol.bound, 0, 1)
        )
        if cort_release > 0.04:
            self.pulses += 1
        return {
            "crh": round(self.crh, 3),
            "acth": round(self.acth, 3),
            "cortisol_bound": round(brain.affect.cortisol.bound, 3),
        }


def receptor_panel(affect) -> dict[str, Any]:
    """Panel α (unión) / β (libre) por neurotransmisor (item 67)."""
    pools = {
        "dopamine": affect.dopamine,
        "serotonin": affect.serotonin,
        "norepinephrine": affect.norepinephrine,
        "oxytocin": affect.oxytocin,
        "cortisol": affect.cortisol,
        "gaba": affect.gaba,
    }
    alpha: dict[str, float] = {}
    beta: dict[str, float] = {}
    for name, pool in pools.items():
        alpha[name] = round(float(pool.bound), 3)
        beta[name] = round(float(np.clip(pool.synaptic * (1.0 - pool.bound), 0, 1)), 3)
    return {"alpha": alpha, "beta": beta}


@dataclass
class AffectDynamicsStack:
    hpa: HPAAxis = field(default_factory=HPAAxis)
    attachment_style: str = ATTACHMENT_SECURE
    shame_level: float = 0.0
    frustration: float = 0.0
    mood_valence_ema: float = 0.0
    mood_label: str = "calm"
    wanting: float = 0.0
    liking: float = 0.0
    empathy_contagion: float = 0.0
    safe_context_ticks: int = 0
    fear_inhibited: bool = False
    last_social_valence: float = 0.0
    last_social_arousal: float = 0.0
    last_metrics: dict[str, Any] = field(default_factory=dict)

    def pfc_amygdala_regulation(self, brain) -> bool:
        """Inhibición top-down de miedo tras contexto seguro (item 69)."""
        if not get_flags(brain).enable_emotion_regulation:
            return False
        room = brain.world.current_room()
        familiar = room in ("casa", "cocina", "dormitorio", "jardín", "sala")
        pain = brain.body.total_pain()
        companion_near = float(np.hypot(
            brain.companion.x - brain.world.agent_x,
            brain.companion.y - brain.world.agent_y,
        )) < 95
        safe = familiar and pain < 0.15 and (companion_near or brain.persona.attachment > 0.45)
        if safe and brain.amygdala.arousal < 0.55:
            self.safe_context_ticks = min(self.safe_context_ticks + 1, 200)
        else:
            self.safe_context_ticks = max(0, self.safe_context_ticks - 2)
        if self.safe_context_ticks >= 8 and brain.amygdala.arousal > 0.35:
            damp = 0.06 + 0.04 * min(self.safe_context_ticks / 40.0, 1.0)
            damp *= 1.0 + 0.25 * brain.modulators.serotonin
            brain.amygdala.arousal = float(np.clip(brain.amygdala.arousal - damp, 0.08, 1))
            brain.amygdala.valence = float(np.clip(brain.amygdala.valence * 0.94 + 0.06, -1, 1))
            self.fear_inhibited = True
            return True
        self.fear_inhibited = False
        return False

    def empathy_contagion_step(self, brain) -> float:
        """Contagio emocional bidireccional Nexo ↔ Nira (item 70)."""
        if not get_flags(brain).enable_empathy_contagion:
            return 0.0
        dist = float(np.hypot(
            brain.companion.x - brain.world.agent_x,
            brain.companion.y - brain.world.agent_y,
        ))
        if dist > 120:
            self.empathy_contagion *= 0.95
            return self.empathy_contagion
        prox = float(np.clip(1.0 - dist / 120.0, 0, 1))
        nira_v = float(getattr(brain.companion.persona, "attachment", 0.4) * 0.3)
        nira_a = 0.35 if brain.companion.persona.mood in ("stressed", "uneasy") else 0.22
        nexo_v = brain.affect.subjective_valence()
        nexo_a = brain.affect.subjective_arousal()
        blend_v = 0.35 * prox * (nira_v - nexo_v)
        blend_a = 0.28 * prox * (nira_a - nexo_a)
        brain.amygdala.valence = float(np.clip(brain.amygdala.valence + blend_v, -1, 1))
        brain.amygdala.arousal = float(np.clip(brain.amygdala.arousal + blend_a, 0, 1))
        brain.companion.persona.mood = brain.chemistry.companion_mood_from_body(
            brain.companion.body.comfort,
            {},
        )
        self.empathy_contagion = float(np.clip(prox * (abs(blend_v) + abs(blend_a)), 0, 1))
        return self.empathy_contagion

    def bowlby_attachment_style(self, brain) -> str:
        """Estilo de apego desde vínculo + cortisol (item 71)."""
        if not get_flags(brain).enable_attachment_style:
            return self.attachment_style
        att = float(brain.persona.attachment)
        cor = float(brain.affect.cortisol.bound)
        if att > 0.52 and cor < 0.48:
            self.attachment_style = ATTACHMENT_SECURE
        elif att > 0.4 and cor > 0.52:
            self.attachment_style = ATTACHMENT_ANXIOUS
        elif att < 0.32:
            self.attachment_style = ATTACHMENT_AVOIDANT
        else:
            self.attachment_style = ATTACHMENT_SECURE
        return self.attachment_style

    def social_shame(self, brain, *, failed: bool, witnessed: bool) -> float:
        """Vergüenza/culpa ante testigo tras fallo (item 72)."""
        if not get_flags(brain).enable_social_shame or not failed or not witnessed:
            self.shame_level = float(np.clip(self.shame_level * 0.92, 0, 1))
            return self.shame_level
        bump = 0.12 + 0.18 * brain.chemistry.proximity
        self.shame_level = float(np.clip(self.shame_level + bump, 0, 1))
        brain.affect.serotonin.release(-0.06)
        brain.affect.cortisol.release(0.04 + self.shame_level * 0.05)
        brain.amygdala.valence = float(np.clip(brain.amygdala.valence - 0.08, -1, 1))
        return self.shame_level

    def split_liking_wanting(self, brain) -> dict[str, float]:
        """μ-opioides (liking) vs DA (wanting) — item 73."""
        if not get_flags(brain).enable_hedonic_wanting:
            return {"liking": self.liking, "wanting": self.wanting}
        h = brain.hedonics
        self.liking = float(np.clip(h.mu_opioid * 0.65 + h.pleasure * 0.35, 0, 1))
        self.wanting = float(
            np.clip(
                0.45 * brain.modulators.dopamine
                + 0.35 * h.craving
                + 0.2 * brain.td_reward.dopamine_pulse()
                if get_flags(brain).enable_td_reward
                else 0.45 * brain.modulators.dopamine + 0.35 * h.craving,
                0,
                1,
            )
        )
        h.craving = float(np.clip(self.wanting * 0.55 + h.craving * 0.45, 0, 1))
        return {"liking": round(self.liking, 3), "wanting": round(self.wanting, 3)}

    def goal_frustration(self, brain, *, stall_ticks: int = 0) -> float:
        """Ira/frustración por meta bloqueada (item 74)."""
        if not get_flags(brain).enable_goal_frustration:
            return self.frustration
        if stall_ticks < 3:
            self.frustration = float(np.clip(self.frustration * 0.9, 0, 1))
            return self.frustration
        self.frustration = float(np.clip(0.15 + stall_ticks * 0.06, 0, 1))
        brain.affect.cortisol.release(0.03 + self.frustration * 0.06)
        brain.affect.norepinephrine.release(0.04 + self.frustration * 0.08)
        brain.amygdala.arousal = float(np.clip(brain.amygdala.arousal + 0.05 * self.frustration, 0, 1))
        brain.amygdala.valence = float(np.clip(brain.amygdala.valence - 0.06 * self.frustration, -1, 1))
        if hasattr(brain, "cingulate") and get_flags(brain).enable_executive_cognition:
            brain.cingulate.conflict_level = float(np.clip(self.frustration * 0.65, 0, 1))
            brain.cingulate.error_signal = float(np.clip(self.frustration * 0.5, 0, 1))
            if hasattr(brain.deliberation, "last"):
                brain.deliberation.last.conflict = max(
                    float(getattr(brain.deliberation.last, "conflict", 0)),
                    brain.cingulate.conflict_level,
                )
        return self.frustration

    def update_mood_inertia(self, brain) -> str:
        """Ánimo persistente con inercia lenta (item 75)."""
        if not get_flags(brain).enable_persistent_mood:
            return brain.persona.mood
        v = brain.affect.subjective_valence()
        a = brain.affect.subjective_arousal()
        self.mood_valence_ema = float(np.clip(0.94 * self.mood_valence_ema + 0.06 * v, -1, 1))
        ema = self.mood_valence_ema
        if ema > 0.35 and a > 0.45:
            label = "excited"
        elif ema > 0.2:
            label = "content"
        elif ema > 0.05:
            label = "curious"
        elif ema < -0.35 and a > 0.5:
            label = "stressed"
        elif ema < -0.15:
            label = "uneasy"
        elif a < 0.25:
            label = "sleepy"
        else:
            label = "calm"
        self.mood_label = label
        brain.persona.mood = label
        if hasattr(brain.companion, "persona"):
            if brain.chemistry.proximity > 0.4:
                brain.companion.persona.mood = brain.chemistry.companion_mood_from_body(
                    brain.companion.body.comfort,
                    {},
                )
        return label

    def social_turn_state(self, brain) -> dict[str, float]:
        """Estado para turno social Nexo↔Nira (item 76)."""
        v = float(
            np.clip(
                0.4 * brain.affect.subjective_valence()
                + 0.3 * brain.amygdala.valence
                + 0.2 * brain.chemistry.last_social_valence
                + 0.1 * self.mood_valence_ema,
                -1,
                1,
            )
        )
        a = float(
            np.clip(
                0.35 * brain.affect.subjective_arousal()
                + 0.3 * brain.amygdala.arousal
                + 0.2 * brain.chemistry.social_arousal
                + 0.15 * self.empathy_contagion,
                0,
                1,
            )
        )
        self.last_social_valence = v
        self.last_social_arousal = a
        return {"valence": v, "arousal": a, "dopamine": float(brain.modulators.dopamine)}

    def post_stimulus(
        self,
        brain,
        *,
        stress: float = 0.0,
        failed_social: bool = False,
        witnessed: bool = False,
        goal_stall_ticks: int = 0,
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_affect_dynamics:
            return {}
        metrics: dict[str, Any] = {}
        if flags.enable_hpa_axis:
            metrics["hpa"] = self.hpa.step(brain, stress=stress)
        if flags.enable_emotion_regulation:
            metrics["fear_inhibited"] = self.pfc_amygdala_regulation(brain)
        if flags.enable_empathy_contagion:
            metrics["empathy"] = round(self.empathy_contagion_step(brain), 3)
        if flags.enable_attachment_style:
            metrics["attachment_style"] = self.bowlby_attachment_style(brain)
        if flags.enable_social_shame:
            metrics["shame"] = round(self.social_shame(brain, failed=failed_social, witnessed=witnessed), 3)
        if flags.enable_hedonic_wanting:
            metrics["motivation"] = self.split_liking_wanting(brain)
        if flags.enable_goal_frustration:
            metrics["frustration"] = round(self.goal_frustration(brain, stall_ticks=goal_stall_ticks), 3)
        if flags.enable_persistent_mood:
            metrics["mood"] = self.update_mood_inertia(brain)
        if flags.enable_receptor_panel:
            metrics["receptors"] = receptor_panel(brain.affect)
        self.last_metrics = metrics
        return metrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachment_style": self.attachment_style,
            "shame_level": round(self.shame_level, 3),
            "frustration": round(self.frustration, 3),
            "mood_valence_ema": round(self.mood_valence_ema, 3),
            "mood_label": self.mood_label,
            "liking": round(self.liking, 3),
            "wanting": round(self.wanting, 3),
            "empathy_contagion": round(self.empathy_contagion, 3),
            "safe_context_ticks": self.safe_context_ticks,
            "fear_inhibited": self.fear_inhibited,
            "hpa": {
                "crh": round(self.hpa.crh, 3),
                "acth": round(self.hpa.acth, 3),
                "pulses": self.hpa.pulses,
            },
            "last_social": {
                "valence": round(self.last_social_valence, 3),
                "arousal": round(self.last_social_arousal, 3),
            },
            "metrics": self.last_metrics,
            "agency_note": "Affect biases drives and chemistry only; PFC selects actions",
        }
