"""Utility AI scoring for creature actions (experimental)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from services.creature.fsm import CreatureState


@dataclass(frozen=True, slots=True)
class WorldCue:
    """Local stimulus snapshot — not a full world simulator (S5)."""

    food_nearby: bool = False
    threat_nearby: bool = False
    agent_nearby: bool = False
    novel_object: bool = False
    shelter_nearby: bool = False


# action -> which drive it primarily services
ACTION_DRIVE: dict[CreatureState, str] = {
    CreatureState.FORAGE: "hunger",
    CreatureState.EAT: "hunger",
    CreatureState.REST: "energy",
    CreatureState.EXPLORE: "exploration",
    CreatureState.FLEE: "fear",
    CreatureState.SOCIALIZE: "sociability",
    CreatureState.INSPECT: "curiosity",
    CreatureState.IDLE: "energy",
}


def score_action(
    action: CreatureState,
    drives: Mapping[str, float],
    personality: Mapping[str, float],
    cue: WorldCue,
) -> float:
    """Higher score = more desirable. Deterministic pure function."""
    drive_key = ACTION_DRIVE[action]
    drive = float(drives.get(drive_key, 0.0))
    score = drive

    # Personality modulators (experimental sliders from Being).
    if action in (CreatureState.EXPLORE, CreatureState.INSPECT):
        score += 0.35 * float(personality.get("curiosity", 0.5))
        score += 0.25 * float(personality.get("exploration", 0.5))
    if action is CreatureState.SOCIALIZE:
        score += 0.4 * float(personality.get("sociability", 0.5))
        score += 0.2 * float(personality.get("trust", 0.5))
    if action is CreatureState.FLEE:
        score += 0.35 * float(personality.get("caution", 0.5))
        score -= 0.15 * float(personality.get("impulsivity", 0.5))
    if action in (CreatureState.FORAGE, CreatureState.EAT):
        score += 0.15 * float(personality.get("persistence", 0.5))
    if action is CreatureState.REST:
        score += 0.2 * float(personality.get("patience", 0.5))

    # Cue bonuses / vetoes.
    if cue.threat_nearby and action is CreatureState.FLEE:
        score += 0.9
    if cue.threat_nearby and action in (CreatureState.EAT, CreatureState.SOCIALIZE, CreatureState.REST):
        score -= 0.8
    if cue.food_nearby and action in (CreatureState.FORAGE, CreatureState.EAT):
        score += 0.55
    if cue.agent_nearby and action is CreatureState.SOCIALIZE:
        score += 0.45
    if cue.novel_object and action is CreatureState.INSPECT:
        score += 0.5
    if cue.shelter_nearby and action is CreatureState.REST and float(drives.get("energy", 1.0)) < 0.4:
        score += 0.35
    if action is CreatureState.IDLE:
        score = 0.15 + 0.1 * float(drives.get("energy", 0.5))

    return float(score)


def choose_action(
    candidates: tuple[CreatureState, ...],
    drives: Mapping[str, float],
    personality: Mapping[str, float],
    cue: WorldCue,
) -> CreatureState:
    if not candidates:
        return CreatureState.IDLE
    ranked = sorted(
        candidates,
        key=lambda a: (-score_action(a, drives, personality, cue), a.value),
    )
    return ranked[0]
