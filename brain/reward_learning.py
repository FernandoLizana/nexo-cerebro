"""
Aprendizaje por recompensa y causalidad — Bloque F (items 57–66).

Acopla TD, sorpresa, affordances, schemas y metaplasticidad.
Nunca escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .experiment_flags import get_flags

# Grupos de transferencia causal (objeto A → B en casa)
CAUSAL_TRANSFER_GROUPS: dict[str, tuple[str, ...]] = {
    "drink": ("fountain", "fridge", "crop", "food_bowl"),
    "eat": ("fridge", "stove", "crop", "food_source", "food_bowl"),
    "hygiene": ("bath", "toilet", "fountain"),
    "rest": ("bed", "sofa"),
}


@dataclass
class BCMMetaplasticity:
    """Umbrales BCM-like — LTP/LTD según actividad media."""

    theta_m: float = 0.48
    plasticity_scale: float = 1.0

    def step(self, brain) -> dict[str, float]:
        activity = float(brain.cortex.associative.spikes.mean())
        self.theta_m = float(np.clip(0.92 * self.theta_m + 0.08 * activity, 0.15, 0.85))
        if activity > self.theta_m + 0.05:
            self.plasticity_scale = float(np.clip(self.plasticity_scale * 0.985, 0.65, 1.2))
        elif activity < self.theta_m - 0.05:
            self.plasticity_scale = float(np.clip(self.plasticity_scale * 1.012, 0.65, 1.25))
        brain.cortex.plasticity_mult = float(
            np.clip(brain.cortex.plasticity_mult * (0.99 + 0.02 * self.plasticity_scale), 0.5, 1.4)
        )
        return {
            "theta_m": round(self.theta_m, 3),
            "plasticity_scale": round(self.plasticity_scale, 3),
            "activity": round(activity, 3),
        }


@dataclass
class RewardLearningStack:
    bcm: BCMMetaplasticity = field(default_factory=BCMMetaplasticity)
    last_rpe_blend: float = 0.0
    latent_probes: int = 0
    transfers_applied: int = 0
    schemas_extinguished: int = 0
    model_based_active: bool = False
    last_metrics: dict[str, Any] = field(default_factory=dict)

    def couple_rpe_surprise(self, brain, *, surprise: float) -> float:
        """Unifica δ dopaminérgico con sorpresa cognitiva (item 58)."""
        if not get_flags(brain).enable_rpe_surprise_coupling:
            return brain.td_reward.last_delta
        td = brain.td_reward
        blend = float(np.clip(0.55 * td.last_delta + 0.45 * (surprise - 0.5), -1, 1))
        self.last_rpe_blend = blend
        td.last_delta = float(np.clip(td.last_delta + 0.22 * (surprise - 0.5), -1.2, 1.2))
        return td.last_delta

    def apply_causal_transfer(self, brain) -> int:
        """Generaliza affordances entre objetos similares (item 61)."""
        if not get_flags(brain).enable_causal_transfer:
            return 0
        am = brain.affordance_map
        applied = 0
        for group in CAUSAL_TRANSFER_GROUPS.values():
            sources = [r for r in am.records.values() if r.object_type in group and r.confidence > 0.25]
            if len(sources) < 1:
                continue
            best = max(sources, key=lambda r: r.confidence * abs(r.mean_homeostasis_gain))
            for target_type in group:
                if target_type == best.object_type:
                    continue
                from .affordance_map import AffordanceRecord

                probe = AffordanceRecord(
                    object_type=target_type,
                    object_id=f"transfer_{target_type}",
                    interaction=best.interaction,
                    candidate_key=best.candidate_key,
                    dominant_drive=best.dominant_drive,
                    room=best.room,
                )
                if probe.key in am.records and am.records[probe.key].observation_count >= 2:
                    continue
                transferred = am.records.get(probe.key)
                if transferred is None:
                    transferred = probe
                    am.records[transferred.key] = transferred
                factor = 0.38
                for name in transferred.expected_outcomes:
                    old = float(transferred.expected_outcomes.get(name, 0))
                    src = float(best.expected_outcomes.get(name, 0))
                    transferred.expected_outcomes[name] = float(old * (1 - factor) + src * factor)
                transferred.mean_homeostasis_gain = float(
                    transferred.mean_homeostasis_gain * (1 - factor)
                    + best.mean_homeostasis_gain * factor
                )
                transferred.observation_count = max(transferred.observation_count, 1)
                transferred.success_count = max(
                    transferred.success_count,
                    int(round(best.success_count * factor)),
                )
                applied += 1
        self.transfers_applied += applied
        if applied:
            am.save()
        return applied

    def latent_affordance_probe(self, brain, *, curiosity: float) -> bool:
        """Exploración sin recompensa — curiosidad actualiza mapa (item 64)."""
        if not get_flags(brain).enable_latent_affordance:
            return False
        if curiosity < 0.42:
            return False
        from .affordance_map import AffordanceRecord

        room = brain.world.current_room()
        am = brain.affordance_map
        for obj in brain.world.objects[:4]:
            for interaction, candidate_key in (("drink", "drink"), ("eat", "eat")):
                probe = AffordanceRecord(
                    object_type=obj.kind,
                    object_id=obj.id,
                    interaction=interaction,
                    candidate_key=candidate_key,
                    dominant_drive="seek_curiosity",
                    room=room,
                )
                rec = am.records.get(probe.key)
                if rec is None:
                    rec = probe
                    am.records[rec.key] = rec
                rec.observation_count += 1
                rec.expected_outcomes["comfort"] = float(
                    rec.expected_outcomes.get("comfort", 0.0) + 0.012 * curiosity
                )
                rec.mean_homeostasis_gain = float(
                    rec.mean_homeostasis_gain + 0.006 * curiosity
                )
        self.latent_probes += 1
        return True

    def tick_schema_extinction(self, brain, *, used_key: str = "") -> int:
        """Decay de schemas no usados (item 63)."""
        if not get_flags(brain).enable_schema_extinction:
            return 0
        sl = brain.schema_learner
        removed = 0
        keep: list = []
        for schema in sl.schemas:
            if schema.key == used_key:
                schema.successes = int(schema.successes) + 1
                keep.append(schema)
                continue
            schema.successes = max(0, int(schema.successes) - 1)
            if schema.successes <= 0 and schema.consolidated:
                removed += 1
                continue
            keep.append(schema)
        sl.schemas = keep
        self.schemas_extinguished += removed
        return removed

    def model_based_pfc_boost(self, brain, contestants: list) -> bool:
        """Cuando affordances son ricas, sesgar PFC (item 65)."""
        if not get_flags(brain).enable_model_based_deliberation:
            self.model_based_active = False
            return False
        am = brain.affordance_map
        rich = sum(1 for r in am.records.values() if r.confidence > 0.3) >= 3
        self.model_based_active = rich
        if not rich:
            return False
        room = brain.world.current_room()
        drives = brain._merged_drives()
        top_drive = max(drives.items(), key=lambda x: x[1])[0] if drives else ""
        biases = am.biases_for(
            candidate_keys=[c.key for c in contestants],
            dominant_drive=top_drive,
            room=room,
        )
        for c in contestants:
            if biases.get(c.key, 0) > 0.02:
                c.pfc = float(np.clip(c.pfc + 0.07 * abs(biases[c.key]), 0, 1.2))
        return True

    def post_act(
        self,
        brain,
        *,
        surprise: float,
        curiosity: float,
        choice_key: str,
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_reward_learning:
            return {}
        metrics: dict[str, Any] = {}
        if flags.enable_td_reward and flags.enable_rpe_surprise_coupling:
            metrics["rpe_delta"] = round(self.couple_rpe_surprise(brain, surprise=surprise), 4)
        if flags.enable_metaplasticity_bcm:
            metrics["bcm"] = self.bcm.step(brain)
        if flags.enable_schema_extinction:
            metrics["schemas_extinguished"] = self.tick_schema_extinction(brain, used_key=choice_key)
        if flags.enable_causal_transfer and brain.lifecycle.age_ticks % 40 == 0:
            metrics["causal_transfers"] = self.apply_causal_transfer(brain)
        if flags.enable_latent_affordance and choice_key in ("wander", "explore", ""):
            metrics["latent_probe"] = self.latent_affordance_probe(brain, curiosity=curiosity)
        self.last_metrics = metrics
        return metrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "rpe_blend": round(self.last_rpe_blend, 4),
            "latent_probes": self.latent_probes,
            "transfers_applied": self.transfers_applied,
            "schemas_extinguished": self.schemas_extinguished,
            "model_based_active": self.model_based_active,
            "bcm": {
                "theta_m": round(self.bcm.theta_m, 3),
                "plasticity_scale": round(self.bcm.plasticity_scale, 3),
            },
            "metrics": self.last_metrics,
        }
