"""Character Creator — build Beings with experimental personality sliders."""

from __future__ import annotations

from typing import Any, Mapping

from services.being.models import (
    EXPERIMENTAL_DISCLAIMER,
    PERSONALITY_TRAITS,
    Being,
    BeingArchetype,
    BeingIdentity,
    BeingSpecies,
    CognitiveConfiguration,
    CorePersonality,
    MemoryBundle,
    TemporaryState,
    _utc_now,
    new_being_id,
)
from services.being.store import BeingStore
from services.being.validation import BeingValidationError


def create_being(
    *,
    name: str,
    species: BeingSpecies | str,
    archetype: BeingArchetype | str = BeingArchetype.CUSTOM,
    creator_node: str,
    traits: Mapping[str, float] | None = None,
    interests: list[str] | None = None,
    goals: list[str] | None = None,
    simulated_fears: list[str] | None = None,
    preferences: list[str] | None = None,
    communication_style: str = "neutral",
    cognitive_budget: float = 1.0,
    memory_level: str = "standard",
    use_llm: bool = False,
    store: BeingStore | None = None,
) -> Being:
    """Create and optionally persist a Being.

    Traits outside ``PERSONALITY_TRAITS`` are rejected.
    """
    species_e = species if isinstance(species, BeingSpecies) else BeingSpecies(str(species))
    archetype_e = (
        archetype if isinstance(archetype, BeingArchetype) else BeingArchetype(str(archetype))
    )
    if not str(name).strip():
        raise BeingValidationError("name required")
    if not str(creator_node).strip():
        raise BeingValidationError("creator_node required")

    personality = CorePersonality.defaults_for(species_e, archetype_e)
    if traits:
        unknown = [k for k in traits if k not in PERSONALITY_TRAITS]
        if unknown:
            raise BeingValidationError(f"unknown personality traits: {unknown}")
        for key, value in traits.items():
            if not 0.0 <= float(value) <= 1.0:
                raise BeingValidationError(f"trait {key} out of bounds: {value}")
        merged = dict(personality.traits)
        merged.update({k: float(v) for k, v in traits.items()})
        personality = CorePersonality(
            traits=merged,
            interests=list(interests or personality.interests),
            goals=list(goals or personality.goals),
            simulated_fears=list(simulated_fears or personality.simulated_fears),
            preferences=list(preferences or personality.preferences),
            communication_style=communication_style,
        ).normalized()
    else:
        personality = CorePersonality(
            traits=personality.traits,
            interests=list(interests or []),
            goals=list(goals or []),
            simulated_fears=list(simulated_fears or []),
            preferences=list(preferences or []),
            communication_style=communication_style,
        ).normalized()

    # Animals default to no LLM — Creature Engine path (S4).
    if species_e in (BeingSpecies.ANIMAL, BeingSpecies.CREATURE) and use_llm is False:
        use_llm = False
        if memory_level == "rich" and cognitive_budget > 0.6:
            cognitive_budget = 0.6
            memory_level = "standard"

    being = Being(
        identity=BeingIdentity(
            being_id=new_being_id(),
            name=str(name).strip(),
            species=species_e,
            archetype=archetype_e,
            creator_node=str(creator_node).strip(),
            created_at=_utc_now(),
            core_personality=personality,
        ),
        memory=MemoryBundle(),
        state=TemporaryState.defaults_for(species_e),
        cognitive=CognitiveConfiguration(
            cognitive_budget=cognitive_budget,
            memory_level=memory_level,
            use_llm=bool(use_llm),
            behavioral_parameters={},
        ),
    )
    if store is not None:
        store.save(being)
    return being


def being_public_summary(being: Being) -> dict[str, Any]:
    return {
        "being_id": being.identity.being_id,
        "name": being.identity.name,
        "species": being.identity.species.value,
        "archetype": being.identity.archetype.value,
        "creator_node": being.identity.creator_node,
        "traits": being.identity.core_personality.traits,
        "cognitive_budget": being.cognitive.cognitive_budget,
        "use_llm": being.cognitive.use_llm,
        "disclaimer": EXPERIMENTAL_DISCLAIMER,
    }
