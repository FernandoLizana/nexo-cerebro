"""
Integración conductual — une PFC, afecto, memoria tipada y currículos.

El mundo ya no elige al azar en el escritorio: la deliberación (`choice_key`)
y el estado cerebral (progreso de tracks, WM, afecto) determinan el evento.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain
    from .world import World2D

# choice_key PFC → tipos de evento permitidos (prioridad)
CHOICE_EVENT_MAP: dict[str, tuple[str, ...]] = {
    "eat": ("eat_cooked", "eat", "cook", "harvest"),
    "cook": ("cook", "eat_cooked", "eat"),
    "harvest": ("harvest", "cook", "eat"),
    "drink": ("drink",),
    "rest": ("rest",),
    "sleep": ("rest",),
    "tv": ("tv_use",),
    "research": ("web_search",),
    "study": (
        "curriculum_study",
        "brain_facts_study",
        "anatomy_study",
        "clinical_study",
        "biopsych_study",
        "infant_study",
        "library_study",
    ),
    "clinical": ("clinical_study",),
    "biopsych": ("biopsych_study",),
    "infant": ("infant_study",),
    "hygiene": ("bathe",),
    "bathroom": ("bathroom",),
    "companion": ("touch",),
    "warmth": ("rest",),
    "relief": ("rest", "bathe"),
}

DESK_STUDY_EVENTS = (
    "curriculum_study",
    "brain_facts_study",
    "anatomy_study",
    "clinical_study",
    "biopsych_study",
    "infant_study",
    "library_study",
    "web_search",
)


def _track_candidates(brain: InfantApeBrain) -> list[tuple[str, float, str]]:
    """(event_type, urgency 0-1, title) — mayor = más pendiente."""
    out: list[tuple[str, float, str]] = []
    pairs = (
        ("curriculum_study", brain.curriculum, "Currículo"),
        ("brain_facts_study", brain.brain_facts, "Brain Facts"),
        ("anatomy_study", brain.anatomy, "Anatomía"),
        ("clinical_study", brain.clinical_neurology, "Manual UDD"),
        ("biopsych_study", brain.biopsych, "Biopsych"),
        ("infant_study", brain.infant_brain, "Infantil"),
    )
    for ev, state, _label in pairs:
        nxt = state.suggest_next()
        if nxt is None:
            continue
        prog = 1.0 - float(state.progress_ratio())
        focus = 0.12 if getattr(state, "focus_ticks", 0) > 0 else 0.0
        urgency = float(np.clip(prog * 0.72 + focus + 0.08, 0.05, 1.0))
        title = getattr(nxt, "title", str(nxt))
        out.append((ev, urgency, title))
    try:
        from .library import list_books

        if list_books():
            out.append(("library_study", 0.22, "Biblioteca"))
    except OSError:
        pass
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def pick_desk_study_event(
    brain: InfantApeBrain,
    *,
    choice_key: str = "",
    curiosity: float = 0.0,
) -> dict[str, Any]:
    """Elige estudio en escritorio según PFC + progreso (sin RNG)."""
    ck = (choice_key or "").strip()
    if ck not in ("clinical", "biopsych", "infant", "research") and curiosity >= 0.45:
        from .node_offerings import peek_offering

        offer = peek_offering()
        if offer:
            return {
                "type": "node_study",
                "target": "escritorio",
                "meta": {"offering_id": offer["id"], "source": "curiosity"},
            }
    if ck == "research" or (ck == "wander" and curiosity > 0.55):
        return {"type": "web_search", "target": "escritorio", "source": "pfc_research"}
    allowed = set(DESK_STUDY_EVENTS)
    if ck in CHOICE_EVENT_MAP:
        allowed = set(CHOICE_EVENT_MAP[ck]) & allowed or allowed
    if ck in ("clinical", "biopsych", "infant"):
        allowed = set(CHOICE_EVENT_MAP.get(ck, ()))

    candidates = [c for c in _track_candidates(brain) if c[0] in allowed]
    if not candidates:
        if "web_search" in allowed and curiosity > 0.2:
            return {"type": "web_search", "target": "escritorio", "source": "curiosity_fallback"}
        return {"type": "curriculum_study", "target": "escritorio", "source": "default"}

    best_ev, score, title = candidates[0]
    if ck == "study" and len(candidates) > 1:
        # Mezcla suave: segundo track si casi empata (memoria procedural / variedad)
        second = candidates[1]
        if second[1] > score * 0.88:
            best_ev, score, title = second

    meta: dict[str, Any] = {"source": "integrated", "pfc": ck or "study", "track_title": title}
    for ev, st in (
        ("clinical_study", brain.clinical_neurology),
        ("biopsych_study", brain.biopsych),
        ("infant_study", brain.infant_brain),
    ):
        if best_ev == ev:
            nxt = st.suggest_next()
            if nxt:
                meta["section_key"] = nxt.key
    return {"type": best_ev, "target": "escritorio", "meta": meta}


def choice_allows_event(choice_key: str, event_type: str) -> bool:
    if not choice_key or choice_key == "wander":
        return True
    allowed = CHOICE_EVENT_MAP.get(choice_key)
    if not allowed:
        return True
    return event_type in allowed


def pre_cognize_interocept(brain: InfantApeBrain, *, surprise: float = 0.0) -> None:
    """Afecto + ínsula ligera antes de deliberar (mismo tick)."""
    body = brain.body
    pain = float(body.total_pain())
    valence = float(brain.amygdala.valence)
    arousal = float(max(brain.amygdala.arousal, brain.brainstem.arousal_bias))
    if pain > 0.15:
        valence = min(valence, -0.1)
        arousal = max(arousal, 0.45)
    brain.affect.process_stimulus(
        valence=valence,
        arousal=arousal,
        novelty=min(0.5, surprise),
        pain=pain,
        social_bond=float(brain.chemistry.seek_companion_drive()) * 0.3,
        attention=float(brain.modulators.acetylcholine),
        surprise=surprise,
    )
    brain.affect.step()
    brain.affect.sync_modulators(brain.modulators)
    if hasattr(brain, "insula"):
        brain.insula.integrate(brain)


def deliberation_track_boost(brain: InfantApeBrain, key: str) -> float:
    """Sesgo limbico extra por tracks incompletos y foco WM."""
    boosts = {
        "study": 0.0,
        "research": 0.0,
        "clinical": 0.0,
        "biopsych": 0.0,
        "infant": 0.0,
    }
    if key in ("study", "research", "clinical", "biopsych", "infant"):
        curiosity = float(brain._merged_drives().get("seek_curiosity", 0))
        boosts["study"] = curiosity * 0.35
        boosts["research"] = curiosity * 0.28
    mapping = {
        "clinical": brain.clinical_neurology,
        "biopsych": brain.biopsych,
        "infant": brain.infant_brain,
    }
    if key in mapping:
        st = mapping[key]
        if st.suggest_next():
            boosts[key] = (1.0 - st.progress_ratio()) * 0.42 + (
                0.1 if st.focus_ticks > 0 else 0.0
            )
    if key == "study":
        for st in (
            brain.curriculum,
            brain.brain_facts,
            brain.anatomy,
            brain.clinical_neurology,
            brain.biopsych,
            brain.infant_brain,
        ):
            if st.suggest_next() and st.progress_ratio() < 0.85:
                boosts["study"] = max(boosts["study"], (1.0 - st.progress_ratio()) * 0.25)
    return float(boosts.get(key, 0.0))


def sleep_study_weights(brain: InfantApeBrain) -> dict[str, float]:
    """Pesos nocturnos alineados al estado de vigilia."""
    base = {
        "repaso": 0.16,
        "curriculum": 0.12,
        "brain_facts": 0.08,
        "anatomy": 0.07,
        "clinical": 0.14,
        "biopsych": 0.12,
        "infant_brain": 0.08,
        "library": 0.08,
        "web": 0.05,
    }
    tracks = (
        ("clinical", brain.clinical_neurology),
        ("biopsych", brain.biopsych),
        ("infant_brain", brain.infant_brain),
    )
    for kind, st in tracks:
        if st.suggest_next():
            base[kind] += (1.0 - st.progress_ratio()) * 0.12
        else:
            base[kind] *= 0.35
    if brain.clinical_neurology.focus_ticks > 0:
        base["clinical"] += 0.08
    if brain.biopsych.focus_ticks > 0:
        base["biopsych"] += 0.08
    curiosity = float(brain._merged_drives().get("seek_curiosity", 0))
    base["web"] += curiosity * 0.08
    base["library"] += curiosity * 0.06
    return base


def tick_study_focus(brain: InfantApeBrain) -> None:
    """Decaimiento de foco en todos los tracks."""
    for st in (
        brain.curriculum,
        brain.brain_facts,
        brain.anatomy,
        brain.clinical_neurology,
        brain.biopsych,
        brain.infant_brain,
    ):
        if hasattr(st, "tick_focus"):
            st.tick_focus()
