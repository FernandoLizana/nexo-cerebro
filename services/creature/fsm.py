"""Finite-state machine for Creature Engine."""

from __future__ import annotations

from enum import Enum


class CreatureState(str, Enum):
    IDLE = "IDLE"
    FORAGE = "FORAGE"
    EAT = "EAT"
    REST = "REST"
    EXPLORE = "EXPLORE"
    FLEE = "FLEE"
    SOCIALIZE = "SOCIALIZE"
    INSPECT = "INSPECT"


TRANSITIONS: dict[CreatureState, frozenset[CreatureState]] = {
    CreatureState.IDLE: frozenset(
        {
            CreatureState.FORAGE,
            CreatureState.EXPLORE,
            CreatureState.REST,
            CreatureState.FLEE,
            CreatureState.SOCIALIZE,
            CreatureState.INSPECT,
            CreatureState.IDLE,
        }
    ),
    CreatureState.FORAGE: frozenset(
        {CreatureState.EAT, CreatureState.EXPLORE, CreatureState.FLEE, CreatureState.IDLE}
    ),
    CreatureState.EAT: frozenset({CreatureState.IDLE, CreatureState.REST, CreatureState.FLEE}),
    CreatureState.REST: frozenset({CreatureState.IDLE, CreatureState.EXPLORE, CreatureState.FLEE}),
    CreatureState.EXPLORE: frozenset(
        {
            CreatureState.INSPECT,
            CreatureState.FORAGE,
            CreatureState.IDLE,
            CreatureState.FLEE,
            CreatureState.SOCIALIZE,
        }
    ),
    CreatureState.FLEE: frozenset({CreatureState.IDLE, CreatureState.REST}),
    CreatureState.SOCIALIZE: frozenset({CreatureState.IDLE, CreatureState.EXPLORE, CreatureState.FLEE}),
    CreatureState.INSPECT: frozenset({CreatureState.IDLE, CreatureState.EXPLORE, CreatureState.FORAGE}),
}


def can_transition(current: CreatureState, nxt: CreatureState) -> bool:
    return nxt in TRANSITIONS.get(current, frozenset())
