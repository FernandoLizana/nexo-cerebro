"""Estados cognitivos tipados e inmutables."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class HomeostaticState:
    energy: float = 1.0
    hydration: float = 1.0
    temperature: float = 37.0
    pain: float = 0.0
    fatigue: float = 0.0
    sleep_pressure: float = 0.0
    stress_load: float = 0.0
    social_need: float = 0.3
    safety_need: float = 0.2

    def clamp(self) -> HomeostaticState:
        return HomeostaticState(
            energy=max(0.0, min(1.0, self.energy)),
            hydration=max(0.0, min(1.0, self.hydration)),
            temperature=max(34.0, min(42.0, self.temperature)),
            pain=max(0.0, min(1.0, self.pain)),
            fatigue=max(0.0, min(1.0, self.fatigue)),
            sleep_pressure=max(0.0, min(1.0, self.sleep_pressure)),
            stress_load=max(0.0, min(1.0, self.stress_load)),
            social_need=max(0.0, min(1.0, self.social_need)),
            safety_need=max(0.0, min(1.0, self.safety_need)),
        )


@dataclass(frozen=True)
class AffectiveState:
    valence: float = 0.0
    arousal: float = 0.2
    dominance: float = 0.5
    uncertainty: float = 0.3
    threat: float = 0.0
    frustration: float = 0.0
    curiosity: float = 0.4
    mood_baseline: float = 0.0


@dataclass(frozen=True)
class CognitiveState:
    tick: int = 0
    simulation_time: float = 0.0
    attention_focus: tuple[str, ...] = ()
    working_memory_items: tuple[tuple[str, float], ...] = ()
    active_goals: tuple[str, ...] = ("survive",)
    current_action: str | None = None
    confidence: float = 0.5
    global_workspace_content: tuple[str, ...] = ()
    homeostatic: HomeostaticState = HomeostaticState()
    affective: AffectiveState = AffectiveState()
    last_reward: float = 0.0
    trajectory_digest: tuple[float, ...] = ()

    def with_homeostatic(self, homeostatic: HomeostaticState) -> CognitiveState:
        return replace(self, homeostatic=homeostatic.clamp())

    def with_affective(self, affective: AffectiveState) -> CognitiveState:
        return replace(self, affective=affective)

    def with_tick(self, tick: int, simulation_time: float) -> CognitiveState:
        return replace(self, tick=tick, simulation_time=simulation_time)
