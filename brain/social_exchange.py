"""
Intercambio social Nexo ↔ Nira — diálogo bidireccional + aprendizaje compartido.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .learning_hub import LearningEvent

if TYPE_CHECKING:
    from .mind import InfantApeBrain


def run_social_exchange(brain: InfantApeBrain, *, trigger: str = "proximity") -> dict[str, Any]:
    """Un turno de conversación verbal: Nexo habla en voz alta, Nira responde."""
    from .experiment_flags import get_flags

    dist = float(
        ((brain.companion.x - brain.world.agent_x) ** 2 + (brain.companion.y - brain.world.agent_y) ** 2) ** 0.5
    )
    flow = brain.thoughts.stream_snapshot(8)
    lctx = brain._language_context(
        ep=brain._last_ep or {},
        draft=brain._state_draft(brain._last_ep or {}),
        mode="world",
        thought_flow=flow,
    )
    exchange = brain.language_network.dyad_exchange(brain, lctx, brain.language)
    nexo_line = exchange.nexo_line
    nira_line = exchange.nira_line
    nx_src = exchange.nexo_source
    nr_src = exchange.nira_source

    # RelationshipModel already updated inside dyad_exchange; retag trigger for social path.
    rel = getattr(brain, "relationship_model", None)
    if rel is not None and hasattr(rel, "cooperation_history") and rel.cooperation_history:
        last = rel.cooperation_history[-1]
        if last.get("domain") == "dialogue" and str(last.get("note", "")).startswith("dyad:"):
            last["note"] = f"dyad:{trigger}"[:200]

    brain.persona.message = nexo_line
    brain.companion.persona.message = nira_line
    brain.persona.add_turn("nexo", nexo_line)
    brain.companion.persona.add_turn("nira", nira_line)

    transcript = f"Nexo: {nexo_line}\nNira: {nira_line}"
    learn_result = brain.learning_hub.learn(
        brain,
        LearningEvent(
            source="social",
            label=f"diálogo con Nira ({trigger})",
            content=transcript,
            modality="social",
            tags=["social", "dialogue", "nira", "nexo", trigger],
            agents=["nexo", "nira"],
            social=True,
            steps_per_repeat=26,
        ),
    )

    for item in learn_result.get("episode_list", []):
        if item.get("agent") == "nexo":
            brain._apply_social_chemistry(item["episode"], social=True)
            brain._last_ep = item["episode"]
            break

    flags = get_flags(brain)
    if flags.enable_social_turns and hasattr(brain, "affect_dynamics"):
        social_state = brain.affect_dynamics.social_turn_state(brain)
    else:
        social_state = {"valence": 0.25, "arousal": 0.45, "dopamine": float(brain.modulators.dopamine)}

    brain.chemistry.on_social_episode(
        valence=float(social_state.get("valence", 0.25)),
        arousal=float(social_state.get("arousal", 0.45)),
        dopamine=float(social_state.get("dopamine", brain.chemistry.dopamine_spike or 0.35)),
        proximity=brain.chemistry.proximity,
    )
    brain.chemistry.sync_persona_attachment(brain.persona, brain.companion.persona)

    turn = {
        "nexo": nexo_line,
        "nira": nira_line,
        "dist": round(dist, 1),
        "trigger": trigger,
        "verbal": True,
        "modality": "speech",
        "sources": {"nexo": nx_src, "nira": nr_src},
    }
    brain._verbal_dialogue_turn = turn
    brain._dialogue_log.insert(0, turn)
    brain._dialogue_log = brain._dialogue_log[:8]
    brain._log_autonomy(f"conversaron en voz alta — Nexo y Nira ({trigger})")
    return {"turn": turn, "learning": learn_result, "event": {"type": "verbal_dialogue", **turn}}
