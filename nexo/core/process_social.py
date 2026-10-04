"""Procesos Sprint 8 — cognición social y lenguaje."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.homeostasis.drives import DriveField
from nexo.language.composer import UtteranceComposer
from nexo.social.agent_model import CaregiverModel
from nexo.social.theory_of_mind import TheoryOfMindEngine


@dataclass
class SocialModelProcess(BaseProcess):
    """Actualiza modelo del cuidador desde el mundo."""

    process_id: str = "social_model"
    period_ticks: int = 3
    priority: int = 69

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        if world is None:
            return []
        model: CaregiverModel = context.config.setdefault("caregiver_model", CaregiverModel())
        agent = model.sync_from_world(world)
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="social.perceived",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload=agent.to_dict(),
            )
        ]


@dataclass
class TheoryOfMindProcess(BaseProcess):
    """Inferencia sobre creencias del cuidador."""

    process_id: str = "theory_of_mind"
    period_ticks: int = 5
    priority: int = 68

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        model: CaregiverModel | None = context.config.get("caregiver_model")
        if model is None:
            return []
        engine: TheoryOfMindEngine = context.config.setdefault("tom_engine", TheoryOfMindEngine())
        drives: DriveField | None = context.config.get("drives")
        state = context.state_store.state
        recent_action = next(
            (
                ev.payload.get("action")
                for ev in reversed(context.state_store.event_log[-8:])
                if ev.event_type == "action.selected"
            ),
            None,
        )
        social_need = state.homeostatic.social_need
        if drives is not None:
            social_need = max(social_need, drives.drives.get("social", 0.0))

        inference = engine.infer(
            caregiver=model.agent,
            social_need=social_need,
            recent_action=str(recent_action) if recent_action else None,
            energy=state.homeostatic.energy,
        )
        context.config["social_action_bias"] = inference.social_action_bias
        context.config["tom_inference"] = inference

        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="social.tom_inferred",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload=inference.to_dict(),
            )
        ]


@dataclass
class SocialExchangeProcess(BaseProcess):
    """Intercambio social tras acercarse al cuidador."""

    process_id: str = "social_exchange"
    period_ticks: int = 1
    priority: int = 50

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        recent = context.state_store.event_log[-6:]
        approach = next(
            (
                ev
                for ev in reversed(recent)
                if ev.event_type == "action.selected" and ev.payload.get("action") == "approach_caregiver"
            ),
            None,
        )
        if approach is None:
            return []

        model: CaregiverModel | None = context.config.get("caregiver_model")
        composer: UtteranceComposer | None = context.config.get("utterance_composer")
        if model is None:
            return []

        already = any(
            ev.event_type == "social.exchange" and ev.tick == approach.tick for ev in context.state_store.event_log
        )
        if already:
            return []

        model.register_interaction()
        agent_line = ""
        if composer and composer.history:
            agent_line = composer.history[-1]
        caregiver_line = ""
        if composer:
            caregiver_line = composer.caregiver_reply(
                agent_utterance=agent_line or "…",
                trust=model.agent.trust,
                social_need=context.state_store.state.homeostatic.social_need,
            )

        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="social.exchange",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload={
                    "agent": agent_line or "…",
                    "caregiver": caregiver_line,
                    "trust": model.agent.trust,
                    "interaction_count": model.interaction_count,
                },
            )
        ]


@dataclass
class LanguageProductionProcess(BaseProcess):
    """Producción de enunciados desde estado interno."""

    process_id: str = "language_production"
    period_ticks: int = 8
    priority: int = 49

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        composer: UtteranceComposer = context.config.setdefault("utterance_composer", UtteranceComposer())
        world = context.config.get("world_state")
        drives: DriveField | None = context.config.get("drives")
        meta = context.config.get("metacognition")
        state = context.state_store.state

        recent_action = next(
            (
                ev.payload.get("action")
                for ev in reversed(context.state_store.event_log[-10:])
                if ev.event_type == "action.selected"
            ),
            None,
        )

        plan = composer.compose(
            drives=drives.drives if drives else {},
            metacognitive_felt=getattr(meta, "felt", "") if meta else "",
            metacognitive_doubt=getattr(meta, "doubt", 0.0) if meta else 0.0,
            workspace_labels=state.global_workspace_content,
            last_action=str(recent_action) if recent_action else None,
            caregiver_present=bool(getattr(world, "caregiver_present", False)) if world else False,
            trust=float(getattr(world, "caregiver_trust", 0.5)) if world else 0.5,
            energy=state.homeostatic.energy,
        )
        if plan is None:
            return []

        tick = context.clock.tick
        context.config["last_utterance"] = plan.text
        return [
            CognitiveEvent(
                event_type="language.produced",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload=plan.to_dict(),
            )
        ]
