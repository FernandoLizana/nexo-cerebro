"""Creature Engine — deterministic tick loop without LLM."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable

from services.being.models import Being, BeingArchetype
from services.creature.fsm import CreatureState, TRANSITIONS, can_transition
from services.creature.memory import AssociativeMemory
from services.creature.utility import WorldCue, choose_action


CREATURE_ARCHETYPES = frozenset(
    {
        BeingArchetype.DOG,
        BeingArchetype.CAT,
        BeingArchetype.CROW,
        BeingArchetype.FOX,
        BeingArchetype.ROBOT,
        BeingArchetype.SLIME,
        BeingArchetype.CUSTOM,
    }
)


@dataclass
class CreatureTickResult:
    tick: int
    state: str
    action: str
    drives: dict[str, float]
    cue: dict[str, bool]
    memory_event: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "state": self.state,
            "action": self.action,
            "drives": dict(self.drives),
            "cue": dict(self.cue),
            "memory_event": self.memory_event,
        }


@dataclass
class CreatureEngine:
    """Runs ANIMAL/CREATURE Beings with FSM + utility AI.

    Hard rule: never calls an LLM.
    """

    being: Being
    seed: int = 0
    state: CreatureState = CreatureState.IDLE
    memory: AssociativeMemory = field(default_factory=AssociativeMemory)
    tick: int = 0
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.being.cognitive.use_llm:
            raise ValueError("CreatureEngine refuses Beings with use_llm=True")
        self._rng = random.Random(int(self.seed))
        # Ensure animal-like drives exist.
        drives = dict(self.being.state.drives)
        for key, default in (
            ("hunger", 0.3),
            ("curiosity", 0.5),
            ("energy", 0.7),
            ("fear", 0.2),
            ("affinity", 0.4),
            ("territoriality", 0.3),
            ("sociability", 0.5),
            ("exploration", 0.5),
        ):
            drives.setdefault(key, default)
        self.being.state.drives = drives

    def _sample_cue(self) -> WorldCue:
        # Deterministic pseudo-environment from RNG + drives (no external I/O).
        hunger = float(self.being.state.drives.get("hunger", 0.0))
        fear = float(self.being.state.drives.get("fear", 0.0))
        return WorldCue(
            food_nearby=self._rng.random() < (0.25 + 0.35 * hunger),
            threat_nearby=self._rng.random() < (0.08 + 0.4 * fear),
            agent_nearby=self._rng.random() < 0.2,
            novel_object=self._rng.random() < (0.15 + 0.3 * float(self.being.state.drives.get("curiosity", 0.0))),
            shelter_nearby=self._rng.random() < 0.3,
        )

    def _candidates(self) -> tuple[CreatureState, ...]:
        allowed = TRANSITIONS.get(self.state, frozenset({CreatureState.IDLE}))
        return tuple(sorted(allowed, key=lambda s: s.value))

    def _apply_action(self, action: CreatureState, cue: WorldCue) -> str | None:
        drives = self.being.state.drives
        memory_event: str | None = None

        # Metabolic / drive dynamics (experimental, not biological fidelity).
        drives["hunger"] = min(1.0, float(drives.get("hunger", 0.0)) + 0.02)
        drives["energy"] = max(0.0, float(drives.get("energy", 1.0)) - 0.015)
        drives["curiosity"] = max(0.0, min(1.0, float(drives.get("curiosity", 0.5)) + self._rng.uniform(-0.02, 0.02)))

        if action is CreatureState.EAT and cue.food_nearby:
            drives["hunger"] = max(0.0, float(drives["hunger"]) - 0.35)
            drives["energy"] = min(1.0, float(drives["energy"]) + 0.15)
            self.memory.learn("food", "eat", 0.25)
            memory_event = "learned:food->eat"
        elif action is CreatureState.FORAGE:
            drives["hunger"] = min(1.0, float(drives["hunger"]) + 0.01)
            drives["exploration"] = min(1.0, float(drives.get("exploration", 0.5)) + 0.03)
            if cue.food_nearby:
                self.memory.learn("scent", "forage", 0.15)
                memory_event = "learned:scent->forage"
        elif action is CreatureState.REST:
            drives["energy"] = min(1.0, float(drives["energy"]) + 0.25)
            drives["fear"] = max(0.0, float(drives.get("fear", 0.0)) - 0.05)
        elif action is CreatureState.FLEE:
            drives["fear"] = max(0.0, float(drives.get("fear", 0.0)) - 0.2)
            drives["energy"] = max(0.0, float(drives["energy"]) - 0.05)
            self.memory.learn("threat", "flee", 0.3)
            memory_event = "learned:threat->flee"
        elif action is CreatureState.EXPLORE:
            drives["exploration"] = min(1.0, float(drives.get("exploration", 0.5)) + 0.05)
            drives["curiosity"] = min(1.0, float(drives.get("curiosity", 0.5)) + 0.03)
            drives["energy"] = max(0.0, float(drives["energy"]) - 0.02)
        elif action is CreatureState.INSPECT and cue.novel_object:
            drives["curiosity"] = max(0.0, float(drives.get("curiosity", 0.5)) - 0.15)
            self.memory.learn("object", "inspect", 0.2)
            memory_event = "learned:object->inspect"
        elif action is CreatureState.SOCIALIZE and cue.agent_nearby:
            drives["sociability"] = min(1.0, float(drives.get("sociability", 0.5)) + 0.05)
            drives["affinity"] = min(1.0, float(drives.get("affinity", 0.4)) + 0.04)
            self.memory.learn("agent", "socialize", 0.2)
            memory_event = "learned:agent->socialize"

        if cue.threat_nearby:
            drives["fear"] = min(1.0, float(drives.get("fear", 0.0)) + 0.25)

        # Associative bias: strengthen fear→flee when recalled under threat.
        recalled, strength = self.memory.recall("threat")
        if cue.threat_nearby and recalled == "flee" and strength > 0.3:
            drives["fear"] = min(1.0, float(drives["fear"]) + 0.05)

        self.memory.decay(0.01)
        self.being.state.drives = {k: float(max(0.0, min(1.0, v))) for k, v in drives.items()}
        self.being.identity.age_ticks = int(self.being.identity.age_ticks) + 1
        return memory_event

    def step(self) -> CreatureTickResult:
        self.tick += 1
        cue = self._sample_cue()
        personality = self.being.identity.core_personality.traits
        chosen = choose_action(self._candidates(), self.being.state.drives, personality, cue)

        # Memory can bias toward flee under threat when legal.
        recalled, strength = self.memory.recall("threat")
        if (
            cue.threat_nearby
            and recalled == "flee"
            and strength >= 0.4
            and can_transition(self.state, CreatureState.FLEE)
        ):
            chosen = CreatureState.FLEE

        if not can_transition(self.state, chosen):
            chosen = CreatureState.IDLE if can_transition(self.state, CreatureState.IDLE) else self.state

        memory_event = self._apply_action(chosen, cue)
        self.state = chosen
        return CreatureTickResult(
            tick=self.tick,
            state=self.state.value,
            action=chosen.value,
            drives=dict(self.being.state.drives),
            cue={
                "food_nearby": cue.food_nearby,
                "threat_nearby": cue.threat_nearby,
                "agent_nearby": cue.agent_nearby,
                "novel_object": cue.novel_object,
                "shelter_nearby": cue.shelter_nearby,
            },
            memory_event=memory_event,
        )


def run_creature_ticks(
    being: Being,
    *,
    ticks: int,
    seed: int = 0,
    memory: AssociativeMemory | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Run N deterministic ticks; returns trajectory + final drives."""
    if ticks < 1 or ticks > 10_000:
        raise ValueError("ticks must be in [1, 10000]")
    engine = CreatureEngine(being=being, seed=seed, memory=memory or AssociativeMemory())
    trajectory = []
    stopped = False
    for _ in range(ticks):
        if should_stop is not None and should_stop():
            stopped = True
            break
        trajectory.append(engine.step().to_dict())
    return {
        "ok": not stopped,
        "stopped": stopped,
        "being_id": being.identity.being_id,
        "archetype": being.identity.archetype.value,
        "seed": seed,
        "ticks": len(trajectory),
        "ticks_requested": ticks,
        "final_state": engine.state.value,
        "final_drives": dict(being.state.drives),
        "memory": engine.memory.to_dict(),
        "trajectory": trajectory,
        "llm_used": False,
        "engine": "creature-fsm-utility-v1",
    }


def default_cue_schedule_hash(seed: int, ticks: int) -> str:
    """Helper for tests — exposes determinism of RNG stream without running engine."""
    rng = random.Random(seed)
    bits = []
    for _ in range(ticks):
        bits.append(
            "".join(
                "1" if rng.random() < p else "0"
                for p in (0.4, 0.2, 0.2, 0.3, 0.3)
            )
        )
    return "-".join(bits)
