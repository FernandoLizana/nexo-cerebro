"""Bloque F — aprendizaje por recompensa y causalidad (items 57–66)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from brain.affordance_map import AffordanceRecord, AffordanceMap
from brain.experiment_flags import AblationFlags
from brain.learned_schemas import LearnedSchema, SchemaLearner
from brain.reward_learning import RewardLearningStack
from brain.td_reward import TDRewardSystem, TD_GO_BIAS_MAX


def test_td_go_bias_bounded():
    td = TDRewardSystem()
    td.values["cocina|seek_water|4::drink"] = 2.5
    biases = td.go_biases(
        room="cocina",
        top_drive="seek_water",
        hour=12,
        action_keys=["drink", "wander"],
    )
    assert all(abs(v) <= TD_GO_BIAS_MAX + 1e-6 for v in biases.values())


def test_rpe_surprise_coupling():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_td_reward=True,
        enable_reward_learning=True,
        enable_rpe_surprise_coupling=True,
    )
    brain.td_reward.observe(
        prev_room="cocina",
        prev_drive="seek_water",
        action="drink",
        reward=0.1,
        next_room="cocina",
        next_drive="seek_water",
        hour=12,
    )
    base_delta = brain.td_reward.last_delta
    stack = RewardLearningStack()
    stack.couple_rpe_surprise(brain, surprise=0.9)
    assert brain.td_reward.last_delta != base_delta or abs(base_delta) < 0.01


def test_causal_transfer_between_objects():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        enable_reward_learning=True,
        enable_causal_transfer=True,
    )
    rec = AffordanceRecord(
        object_type="fountain",
        object_id="f1",
        interaction="drink",
        candidate_key="drink",
        dominant_drive="seek_water",
        room="jardin",
    )
    rec.observation_count = 5
    rec.success_count = 4
    rec.mean_homeostasis_gain = 0.12
    rec.expected_outcomes["thirst"] = -0.08
    brain.affordance_map.records[rec.key] = rec
    stack = RewardLearningStack()
    applied = stack.apply_causal_transfer(brain)
    assert applied >= 1
    transferred = [
        r for r in brain.affordance_map.records.values() if r.object_type == "fridge"
    ]
    assert transferred


def test_latent_affordance_probe():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE
    from brain.world import WorldObject

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        enable_reward_learning=True,
        enable_latent_affordance=True,
    )
    brain.world.objects.append(
        WorldObject(id="fr1", kind="fridge", x=100, y=100, label="nevera")
    )
    stack = RewardLearningStack()
    assert stack.latent_affordance_probe(brain, curiosity=0.7)
    assert stack.latent_probes == 1
    assert len(brain.affordance_map.records) >= 1


def test_schema_extinction():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_learned_schemas=True,
        enable_reward_learning=True,
        enable_schema_extinction=True,
    )
    brain.schema_learner.schemas = [
        LearnedSchema(
            key="learned_old",
            label="hábito viejo",
            drive="seek_food",
            target="fridge",
            parent_key="eat",
            successes=1,
            motor_affinity=[4],
            consolidated=True,
        )
    ]
    stack = RewardLearningStack()
    removed = stack.tick_schema_extinction(brain, used_key="eat")
    assert removed == 1
    assert not brain.schema_learner.schemas


def test_model_based_pfc_boost():
    from brain.deliberation import ActionContestant

    class FakeBrain:
        experiment_flags = replace(
            AblationFlags(),
            enable_reward_learning=True,
            enable_model_based_deliberation=True,
            enable_affordance_learning=True,
        )

        class world:
            @staticmethod
            def current_room():
                return "cocina"

        def _merged_drives(self):
            return {"seek_water": 0.6}

        affordance_map = AffordanceMap()

    brain = FakeBrain()
    for i in range(3):
        rec = AffordanceRecord(
            object_type="fountain",
            object_id=f"f{i}",
            interaction="drink",
            candidate_key="drink",
            dominant_drive="seek_water",
            room="cocina",
        )
        rec.observation_count = 4
        rec.success_count = 3
        rec.mean_homeostasis_gain = 0.15
        brain.affordance_map.records[rec.key] = rec
    contestants = [
        ActionContestant(key="drink", label="beber", drive="seek_water", limbic=0.3, pfc=0.2, habit=0.1, go=0.2),
        ActionContestant(key="wander", label="deambular", drive="", limbic=0.1, pfc=0.1, habit=0.0, go=0.1),
    ]
    pfc_before = contestants[0].pfc
    stack = RewardLearningStack()
    assert stack.model_based_pfc_boost(brain, contestants)
    assert contestants[0].pfc > pfc_before


def test_bcm_metaplasticity_step():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_reward_learning=True,
        enable_metaplasticity_bcm=True,
    )
    before = brain.cortex.plasticity_mult
    stack = RewardLearningStack()
    out = stack.bcm.step(brain)
    assert "theta_m" in out
    assert brain.cortex.plasticity_mult != before or before == brain.cortex.plasticity_mult


def test_td_hud_top_values():
    td = TDRewardSystem()
    td.observe(
        prev_room="cocina",
        prev_drive="seek_food",
        action="eat",
        reward=0.4,
        next_room="cocina",
        next_drive="seek_food",
        hour=14,
    )
    hud = td.to_dict()
    assert "top_v" in hud
    assert "last_delta" in hud
    assert hud["go_bias_max"] == TD_GO_BIAS_MAX
