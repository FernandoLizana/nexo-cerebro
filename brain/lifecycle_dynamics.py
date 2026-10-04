"""
Dinámica de sueño, desarrollo y ciclo vital — Bloque J (items 93–97).

NREM/REM completo, estudio nocturno, plasticidad vital, pubertad y envejecimiento.
Nunca escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .experiment_flags import get_flags


@dataclass
class LifecycleDynamicsStack:
    sleep_timeline: list[dict[str, Any]] = field(default_factory=list)
    nocturnal_sessions: int = 0
    last_sleep_summary: dict[str, Any] = field(default_factory=dict)
    pfc_compensation: float = 0.0
    recall_aging_penalty: float = 0.0
    last_metrics: dict[str, Any] = field(default_factory=dict)

    def run_full_sleep_cycle(
        self,
        brain,
        *,
        cycles: int = 3,
        replay_mode: str | None = None,
    ) -> dict[str, Any]:
        """Arquitectura NREM/REM completa con timeline (item 93)."""
        if not get_flags(brain).enable_full_sleep_architecture:
            return {}
        mode = replay_mode or ("selective" if get_flags(brain).enable_selective_sleep else "default")
        out = brain.sleep(cycles=cycles, steps_per_cycle=120, replay_mode=mode)
        timeline = []
        for row in out.get("sleep_phases") or []:
            timeline.append(
                {
                    "cycle": row.get("cycle"),
                    "phase": row.get("phase"),
                    "replays": row.get("replays", 0),
                    "swr": row.get("swr", 0),
                    "consolidated": row.get("consolidated", 0),
                }
            )
        self.sleep_timeline.extend(timeline)
        self.sleep_timeline = self.sleep_timeline[-48:]
        self.last_sleep_summary = {
            "replays": out.get("replays", 0),
            "swr_bursts": out.get("swr_bursts", 0),
            "replay_mode": out.get("replay_mode", mode),
            "phases": len(timeline),
        }
        return out

    def maybe_trigger_sleep(self, brain, *, hour: int, sleep_need: float) -> dict[str, Any] | None:
        if not get_flags(brain).enable_full_sleep_architecture:
            return None
        night = hour >= 22 or hour < 6
        if not night or sleep_need < 0.62:
            return None
        if str(getattr(brain.deliberation.last, "choice_key", "")) not in ("rest", "sleep", ""):
            return None
        return self.run_full_sleep_cycle(brain)

    def tick_nocturnal_study(self, brain, *, phase: str = "rem") -> dict[str, Any]:
        """Estudio autónomo nocturno con pesos por tracks (item 94)."""
        if not get_flags(brain).enable_nocturnal_study:
            return {}
        from .behavior_integration import sleep_study_weights

        weights = sleep_study_weights(brain)
        out: dict[str, Any] = {"weights": {k: round(v, 3) for k, v in list(weights.items())[:8]}}
        if get_flags(brain).enable_sleep_study and hasattr(brain, "sleep_study"):
            if phase == "rem":
                row = brain.sleep_study.maybe_study_during_rem(brain, cycle=1, phase=phase)
                if row:
                    out["rem_study"] = row.to_dict() if hasattr(row, "to_dict") else row
            else:
                session = brain.sleep_study.run_sleep_session(brain, max_actions=1)
                out["session"] = session
            self.nocturnal_sessions += 1
        if get_flags(brain).enable_sleep_web:
            out["web_enabled"] = True
        return out

    def apply_lifecycle_stages(self, brain) -> dict[str, float]:
        """Plasticidad por etapa vital ON (item 95)."""
        if not get_flags(brain).enable_lifecycle_stages:
            return brain.lifecycle.neuro_modulation()
        lc = brain.lifecycle
        lc._update_stage()
        neuro = lc.epigenetic_profile() if get_flags(brain).enable_lifecycle_plasticity else lc.neuro_modulation()
        if get_flags(brain).enable_lifecycle_plasticity:
            brain.cortex.plasticity_mult = float(
                brain.profile.plasticity_mult * neuro.get("expression_plasticity", neuro.get("plasticity_scale", 1.0))
            )
        return neuro

    def apply_puberty_hormones(self, brain) -> dict[str, float]:
        """Moduladores adolescentes — impulsividad PFC (item 96)."""
        if not get_flags(brain).enable_puberty_hormones:
            return {}
        if brain.lifecycle.stage != "adolescente":
            return {}
        brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + 0.04, 0, 1))
        brain.modulators.norepinephrine = float(np.clip(brain.modulators.norepinephrine + 0.03, 0, 1))
        pfc_scale = float(brain.lifecycle.neuro_modulation().get("pfc_inhibition_scale", 0.88))
        return {
            "dopamine": round(brain.modulators.dopamine, 3),
            "pfc_inhibition_scale": round(pfc_scale * 0.82, 3),
            "stage": "adolescente",
        }

    def apply_cognitive_aging(self, brain) -> dict[str, float]:
        """WM ↓, recall ↓, compensación PFC ↑ en anciano (item 97)."""
        if not get_flags(brain).enable_cognitive_aging:
            self.pfc_compensation = 0.0
            self.recall_aging_penalty = 0.0
            return {}
        if brain.lifecycle.stage != "anciano":
            self.pfc_compensation = 0.0
            self.recall_aging_penalty = 0.0
            return {}
        wm = brain.working_memory
        base_cap = wm.effective_capacity()
        aged_cap = max(4, int(base_cap * 0.72))
        wm.capacity = aged_cap
        if not wm.limited:
            wm.limited = True
        self.recall_aging_penalty = float(np.clip(0.08 + (brain.lifecycle.age_years - 55) * 0.004, 0.08, 0.22))
        self.pfc_compensation = float(np.clip(0.06 + (brain.lifecycle.age_years - 55) * 0.003, 0.06, 0.18))
        return {
            "wm_capacity": wm.effective_capacity(),
            "recall_penalty": round(self.recall_aging_penalty, 3),
            "pfc_compensation": round(self.pfc_compensation, 3),
        }

    def deliberation_aging_boost(self, brain, contestants: list) -> bool:
        if self.pfc_compensation <= 0 or not contestants:
            return False
        pfc_top = max(contestants, key=lambda c: c.pfc)
        for c in contestants:
            if c.key == pfc_top.key:
                c.pfc = float(np.clip(c.pfc + self.pfc_compensation, 0, 1.3))
        return True

    def post_tick(
        self,
        brain,
        *,
        hour: int = 12,
        sleep_need: float = 0.0,
        sleep_phase: str = "awake",
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_lifecycle_dynamics:
            return {}
        metrics: dict[str, Any] = {}
        if flags.enable_lifecycle_stages or flags.enable_lifecycle_plasticity:
            metrics["neuro"] = self.apply_lifecycle_stages(brain)
        if flags.enable_puberty_hormones:
            pub = self.apply_puberty_hormones(brain)
            if pub:
                metrics["puberty"] = pub
        if flags.enable_cognitive_aging:
            metrics["aging"] = self.apply_cognitive_aging(brain)
        if flags.enable_nocturnal_study and (hour >= 22 or hour < 6):
            metrics["nocturnal_study"] = self.tick_nocturnal_study(
                brain, phase="rem" if sleep_phase == "rem" else "nrem"
            )
        if flags.enable_full_sleep_architecture:
            triggered = self.maybe_trigger_sleep(brain, hour=hour, sleep_need=sleep_need)
            if triggered:
                metrics["sleep_triggered"] = True
        self.last_metrics = metrics
        return metrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "sleep_timeline": self.sleep_timeline[-12:],
            "last_sleep": self.last_sleep_summary,
            "nocturnal_sessions": self.nocturnal_sessions,
            "pfc_compensation": round(self.pfc_compensation, 3),
            "recall_aging_penalty": round(self.recall_aging_penalty, 3),
            "metrics": self.last_metrics,
            "agency_note": "Sleep and development bias plasticity only; PFC selects actions",
        }
