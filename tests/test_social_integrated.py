"""Tests Sprint 8 — cognición social y lenguaje."""

from __future__ import annotations

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.language.composer import UtteranceComposer
from nexo.social.agent_model import CaregiverModel
from nexo.social.theory_of_mind import TheoryOfMindEngine


def test_caregiver_model_syncs_trust():
    from nexo.demo.room_scenario import RoomWorld

    world = RoomWorld(caregiver_trust=0.8, caregiver_present=True)
    model = CaregiverModel()
    agent = model.sync_from_world(world)
    assert agent.trust == 0.8
    assert agent.presence == 1.0
    assert agent.inferred_intent == "support"


def test_tom_boosts_approach_when_social_need_high():
    from nexo.social.agent_model import SocialAgent

    engine = TheoryOfMindEngine()
    inference = engine.infer(
        caregiver=SocialAgent(trust=0.7, presence=1.0, help_availability=0.6),
        social_need=0.7,
        recent_action=None,
        energy=0.5,
    )
    assert inference.confidence > 0.5
    assert inference.social_action_bias.get("approach_caregiver", 0.0) > 0.0


def test_utterance_composer_hunger():
    composer = UtteranceComposer()
    plan = composer.compose(
        drives={"hunger": 0.7},
        metacognitive_felt="difuso",
        metacognitive_doubt=0.1,
        workspace_labels=(),
        last_action=None,
        caregiver_present=True,
        trust=0.6,
        energy=0.3,
    )
    assert plan is not None
    assert "hambre" in plan.text.lower()


def test_integrated_social_emits_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=40,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            consciousness_mode="integrated",
            social_mode="integrated",
            profile="test_v8",
        )
    )
    result = rt.run()
    types = {e.event_type for e in rt.state_store.event_log}
    assert "social.perceived" in types
    assert "social.tom_inferred" in types
    assert result["social_mode"] == "integrated"
    assert result["tom_inferences"] > 0


def test_social_integrated_vs_legacy_metrics():
    legacy = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=50,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            consciousness_mode="integrated",
            social_mode="legacy",
        )
    ).run()
    integrated = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=50,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            consciousness_mode="integrated",
            social_mode="integrated",
        )
    ).run()
    assert legacy["tom_inferences"] == 0
    assert integrated["tom_inferences"] > 0
    assert integrated["language_utterances"] >= 0


def test_social_reproducible():
    cfg = dict(
        seed=33,
        ticks=35,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        learning_mode="integrated",
        consciousness_mode="integrated",
        social_mode="integrated",
    )
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    assert r1["trajectory_hash"] == r2["trajectory_hash"]
    assert r1["tom_inferences"] == r2["tom_inferences"]


def test_integrated_v8_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v8.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v8"
    assert result["social_mode"] == "integrated"
