"""Integer Creature Engine shared by Python tests and the Android APK.

This is NOT a bit-identical port of services/creature/engine.py.
That engine uses Python random.Random and IEEE floats, which diverge on Kotlin.
Job payloads must set engine=creature-mobile-tier0-v1. The float engine is untouched.
"""

from __future__ import annotations

from typing import Any

from protocols.mobile import ENGINE_ID

MAX_TICKS = 200
MAX_EVENTS = 64
TRANSITIONS: dict[str, frozenset[str]] = {
    "IDLE": frozenset({"FORAGE", "EXPLORE", "REST", "FLEE", "SOCIALIZE", "INSPECT", "IDLE"}),
    "FORAGE": frozenset({"EAT", "EXPLORE", "FLEE", "IDLE"}),
    "EAT": frozenset({"IDLE", "REST", "FLEE"}),
    "REST": frozenset({"IDLE", "EXPLORE", "FLEE"}),
    "EXPLORE": frozenset({"INSPECT", "FORAGE", "IDLE", "FLEE"}),
    "FLEE": frozenset({"IDLE", "REST"}),
    "SOCIALIZE": frozenset({"IDLE", "EXPLORE", "FLEE"}),
    "INSPECT": frozenset({"EXPLORE", "IDLE", "FLEE"}),
}
ACTIONS = (
    "EAT",
    "EXPLORE",
    "FLEE",
    "FORAGE",
    "IDLE",
    "INSPECT",
    "REST",
    "SOCIALIZE",
)


def xorshift32(state: int) -> tuple[int, int]:
    x = state & 0xFFFFFFFF
    if x == 0:
        x = 0x6D2B79F5
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= x >> 17
    x ^= (x << 5) & 0xFFFFFFFF
    x &= 0xFFFFFFFF
    return x, x


def _clamp(value: int) -> int:
    return max(0, min(1000, value))


def run_mobile_creature(
    *,
    seed: int,
    ticks: int,
    being_id: str,
    traits: dict[str, int] | None = None,
) -> dict[str, Any]:
    if ticks < 1 or ticks > MAX_TICKS:
        raise ValueError(f"ticks must be 1..{MAX_TICKS}")
    traits = {k: int(v) for k, v in (traits or {}).items()}
    state_rng = int(seed) & 0xFFFFFFFF
    drives = {
        "hunger": 300,
        "curiosity": 500,
        "energy": 700,
        "fear": 200,
        "sociability": int(traits.get("sociability", 500)),
        "exploration": int(traits.get("exploration", 500)),
    }
    fsm = "IDLE"
    trajectory: list[dict[str, Any]] = []
    events: list[str] = []
    for tick in range(1, ticks + 1):
        state_rng, draw = xorshift32(state_rng)
        cue = {
            "food": bool(draw & 1),
            "threat": bool(draw & 2),
            "agent": bool(draw & 4),
            "novel": bool(draw & 8),
        }
        best = None
        best_score = -10_000
        for action in ACTIONS:
            if action not in TRANSITIONS[fsm] and action != fsm:
                continue
            score = drives.get(
                {
                    "FORAGE": "hunger",
                    "EAT": "hunger",
                    "REST": "energy",
                    "EXPLORE": "exploration",
                    "FLEE": "fear",
                    "SOCIALIZE": "sociability",
                    "INSPECT": "curiosity",
                    "IDLE": "energy",
                }[action],
                0,
            )
            if cue["threat"] and action == "FLEE":
                score += 900
            if cue["threat"] and action in {"EAT", "SOCIALIZE", "REST"}:
                score -= 800
            if cue["food"] and action in {"FORAGE", "EAT"}:
                score += 550
            if cue["agent"] and action == "SOCIALIZE":
                score += 450
            if cue["novel"] and action == "INSPECT":
                score += 500
            if action == "IDLE":
                score = 150
            if best is None or score > best_score or (score == best_score and action < best):
                best = action
                best_score = score
        assert best is not None
        fsm = best
        if fsm == "EAT":
            drives["hunger"] = _clamp(drives["hunger"] - 120)
            drives["energy"] = _clamp(drives["energy"] + 20)
        elif fsm == "FLEE":
            drives["fear"] = _clamp(drives["fear"] - 80)
            drives["energy"] = _clamp(drives["energy"] - 40)
        elif fsm == "REST":
            drives["energy"] = _clamp(drives["energy"] + 90)
        elif fsm == "FORAGE":
            drives["hunger"] = _clamp(drives["hunger"] + 40)
            drives["energy"] = _clamp(drives["energy"] - 15)
        elif fsm == "EXPLORE":
            drives["exploration"] = _clamp(drives["exploration"] - 10)
            drives["energy"] = _clamp(drives["energy"] - 10)
        event = f"{tick}:{fsm}"
        if len(events) < MAX_EVENTS:
            events.append(event)
        trajectory.append({"tick": tick, "state": fsm, "score": best_score, "cue": cue})
    return {
        "ok": True,
        "engine": ENGINE_ID,
        "being_id": being_id,
        "seed": int(seed),
        "ticks": ticks,
        "final_state": fsm,
        "final_drives": drives,
        "events": events,
        "trajectory": trajectory,
        "llm_used": False,
    }
