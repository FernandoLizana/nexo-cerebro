"""Named-character autonomy over personality_archetypes.decide.

Character rejection never implies device disconnect.
"""

from __future__ import annotations

from typing import Any

from .personality_archetypes import NEXUS_PROFILE, NIRA_PROFILE, decide

POLICY_VERSION = "character-autonomy-v1"

_CHARACTER_ALIASES: dict[str, str] = {}
for _alias in NEXUS_PROFILE.get("aliases", ()):
    _CHARACTER_ALIASES[str(_alias).lower()] = "nexus"
for _alias in NIRA_PROFILE.get("aliases", ()):
    _CHARACTER_ALIASES[str(_alias).lower()] = "nira"

# Branch / node ids map to nexus (active) by default; still named for logs.
_BRANCH_DEFAULT = "nexus"

_DECISION_LOG: list[dict[str, Any]] = []


def resolve_character(name: str) -> str:
    key = str(name or "").strip().lower()
    if key in _CHARACTER_ALIASES:
        return _CHARACTER_ALIASES[key]
    if key.startswith("rama") or key.startswith("android") or key.startswith("branch"):
        return key  # keep branch id as character name for logging
    return key or "nexus"


def default_archetype(character: str) -> str | None:
    ch = resolve_character(character)
    if ch == "nira":
        return "mystic"
    if ch == "nexus":
        return "outlaw"
    return None


def evaluate_proposal(
    character: str,
    proposal: str,
    *,
    trust: float = 0.5,
    resources_ok: bool = True,
    archetype: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Decide on a proposal. Rejection does not change connection status."""
    resolved = resolve_character(character)
    used_archetype = archetype if archetype is not None else default_archetype(resolved)
    raw = decide(
        archetype=used_archetype,
        proposal=proposal,
        trust=trust,
        resources_ok=resources_ok,
        seed=seed,
    )
    entry = {
        "character": resolved,
        "character_input": character,
        "proposal": proposal,
        "options_considered": dict(raw.get("options") or {}),
        "factors": {
            "trust": trust,
            "resources_ok": resources_ok,
            "archetype": used_archetype,
            "seed": seed,
        },
        "choice": raw.get("choice"),
        "character_choice": raw.get("choice"),
        "policy_version": POLICY_VERSION,
        "archetype_policy": raw.get("policy_version"),
        "connection_status_unchanged": True,
        "device_available": True,
        "note": "character_decision_only_not_disconnect",
    }
    _DECISION_LOG.insert(0, entry)
    del _DECISION_LOG[64:]
    return entry


def evaluate_node_offer(
    *,
    character: str = "nexus",
    offering_name: str,
    source: str = "nodo",
    trust: float = 0.5,
    resources_ok: bool = True,
    archetype: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Hook for collective_capacity / node_offerings when work is offered."""
    proposal = f"estudiar material de nodo '{offering_name}' (fuente={source})"
    return evaluate_proposal(
        character,
        proposal,
        trust=trust,
        resources_ok=resources_ok,
        archetype=archetype,
        seed=seed,
    )


def recent_decisions(limit: int = 8) -> list[dict[str, Any]]:
    return list(_DECISION_LOG[: max(0, limit)])


def clear_decision_log() -> None:
    _DECISION_LOG.clear()
