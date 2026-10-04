"""Jung-inspired personality archetypes as configurable design presets.

Design bias for simulated decisions — not clinical typology, not astrology,
not fortune-telling. Legacy zodiac keys remain as aliases for saved state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ArchetypePreset:
    key: str
    name_es: str
    jung_focus: str
    tendency: str
    tension: str
    traits: dict[str, float] = field(default_factory=dict)
    decision_bias: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name_es": self.name_es,
            "jung_focus": self.jung_focus,
            "tendency": self.tendency,
            "tension": self.tension,
            "traits": dict(self.traits),
            "decision_bias": dict(self.decision_bias),
        }


ARCHETYPE_PRESETS: dict[str, ArchetypePreset] = {
    "hero": ArchetypePreset(
        "hero", "El Héroe", "Self / impulso consciente",
        "Iniciativa, decisión y estructura",
        "Impulsividad e imposición",
        {"impulsivity": 0.72, "curiosity": 0.55, "patience": 0.28, "cooperation": 0.4},
        {"accept": 0.2, "reject": -0.05, "postpone": -0.15},
    ),
    "sage": ArchetypePreset(
        "sage", "El Sabio", "Senex / discriminación",
        "Análisis, verificación y profundidad",
        "Perfeccionismo y parálisis por análisis",
        {"caution": 0.75, "patience": 0.65, "curiosity": 0.55, "impulsivity": 0.2},
        {"accept": -0.1, "postpone": 0.2, "ask_info": 0.25},
    ),
    "caregiver": ArchetypePreset(
        "caregiver", "El Cuidador", "Great Mother / vínculo",
        "Protección de vínculos y perseverancia compartida",
        "Sobreprotección y actitud defensiva",
        {"cooperation": 0.72, "caution": 0.55, "sociability": 0.65, "patience": 0.5},
        {"accept": 0.1, "reject": 0.05, "ask_info": 0.15},
    ),
    "explorer": ArchetypePreset(
        "explorer", "El Explorador", "Puer / apertura",
        "Exploración e integración de conocimientos",
        "Generalización sin suficiente evidencia",
        {"exploration": 0.8, "curiosity": 0.75, "impulsivity": 0.5, "patience": 0.35},
        {"accept": 0.2, "postpone": -0.1, "ask_info": 0.05},
    ),
    "creator": ArchetypePreset(
        "creator", "El Creador", "Persona expresiva",
        "Coraje, expresión y regulación de impulsos",
        "Necesidad excesiva de reconocimiento",
        {"impulsivity": 0.55, "sociability": 0.7, "curiosity": 0.5, "persistence": 0.6},
        {"accept": 0.15, "reject": 0.05, "negotiate": 0.1},
    ),
    "ruler": ArchetypePreset(
        "ruler", "El Soberano", "Self estructurante",
        "Comprensión de incentivos, recursos y dependencias",
        "Apego al control y a las recompensas",
        {"persistence": 0.75, "caution": 0.6, "patience": 0.55, "impulsivity": 0.25},
        {"accept": 0.05, "reject": 0.1, "ask_info": 0.2},
    ),
    "magician": ArchetypePreset(
        "magician", "El Mago", "Trickster / transformación",
        "Transformación y abandono de patrones obsoletos",
        "Descartar demasiado pronto",
        {"persistence": 0.7, "caution": 0.55, "curiosity": 0.6, "impulsivity": 0.4},
        {"reject": 0.15, "accept": 0.05, "negotiate": 0.1},
    ),
    "lover": ArchetypePreset(
        "lover", "El Amante", "Anima/Animus relacional",
        "Comparación de alternativas y perspectivas",
        "Dispersión e indecisión",
        {"curiosity": 0.75, "impulsivity": 0.48, "patience": 0.35, "exploration": 0.7},
        {"accept": 0.0, "negotiate": 0.25, "postpone": 0.1},
    ),
    "everyman": ArchetypePreset(
        "everyman", "El Ciudadano", "Persona social",
        "Evaluación, reciprocidad y mediación",
        "Indecisión y búsqueda artificial de equilibrio",
        {"cooperation": 0.7, "patience": 0.55, "caution": 0.5, "sociability": 0.65},
        {"negotiate": 0.3, "postpone": 0.15, "accept": 0.0},
    ),
    "innocent": ArchetypePreset(
        "innocent", "El Inocente", "Child / apertura",
        "Continuidad, aprendizaje acumulado y estabilidad",
        "Rigidez y resistencia al cambio",
        {"patience": 0.7, "curiosity": 0.35, "impulsivity": 0.22, "cooperation": 0.5},
        {"accept": 0.05, "reject": 0.1, "postpone": 0.15},
    ),
    "outlaw": ArchetypePreset(
        "outlaw", "El Rebelde", "Shadow / ruptura",
        "Innovación y posibilidades colectivas",
        "Idealismo desconectado de resultados",
        {"curiosity": 0.7, "exploration": 0.75, "cooperation": 0.55, "impulsivity": 0.4},
        {"accept": 0.15, "negotiate": 0.15, "postpone": 0.05},
    ),
    "mystic": ArchetypePreset(
        "mystic", "El Introspectivo", "Anima receptiva",
        "Asociación, sensibilidad al contexto e imaginación",
        "Confundir interpretación con hechos",
        {"curiosity": 0.6, "sociability": 0.55, "patience": 0.5, "caution": 0.45},
        {"postpone": 0.1, "ask_info": 0.2, "accept": 0.05},
    ),
}

NEXUS_PROFILE = {
    "aliases": ("nexus", "nexo"),
    "role": "active_consciousness",
    "archetype_key": "self",
    "archetype_name": "El Sí-mismo (Self)",
    "jung_focus": "integración consciente",
    "learning": "active",
    "cycle": ("goal", "hypothesis", "authorized_action", "observation", "evaluation", "learning"),
}

NIRA_PROFILE = {
    "aliases": ("nira",),
    "role": "receptive_subconscious",
    "archetype_key": "anima",
    "archetype_name": "Ánima receptiva",
    "jung_focus": "observación, asociación, consolidación",
    "learning": "receptive",
    "cycle": (
        "authorized_experience",
        "observation",
        "association",
        "consolidation",
        "hypothesis",
        "optional_verification",
    ),
}

POLICY_VERSION = "jung-archetype-autonomy-v1"


def resolve_key(name: str | None) -> str:
    return str(name or "").strip().lower()


def get_preset(name: str) -> ArchetypePreset | None:
    return ARCHETYPE_PRESETS.get(resolve_key(name))


def all_presets() -> list[ArchetypePreset]:
    order = (
        "hero", "innocent", "lover", "caregiver", "creator", "sage",
        "everyman", "magician", "explorer", "ruler", "outlaw", "mystic",
    )
    return [ARCHETYPE_PRESETS[k] for k in order]


def decide(
    *,
    archetype: str | None = None,
    proposal: str,
    trust: float = 0.5,
    resources_ok: bool = True,
    seed: int | None = None,
) -> dict[str, Any]:
    """Simulated autonomy: accept / reject / negotiate / postpone / ask_info / rest.

    Character decision ≠ user authorization ≠ device availability.
    """
    import random

    rng = random.Random(seed)
    options = ["accept", "reject", "negotiate", "postpone", "ask_info", "rest"]
    scores = {opt: 0.15 + rng.random() * 0.05 for opt in options}
    preset = get_preset(archetype or "")
    if preset:
        for key, bias in preset.decision_bias.items():
            if key in scores:
                scores[key] += float(bias)
        if preset.traits.get("caution", 0) > 0.6:
            scores["ask_info"] += 0.1
            scores["accept"] -= 0.05
        if preset.traits.get("impulsivity", 0) > 0.6:
            scores["accept"] += 0.1
            scores["postpone"] -= 0.1
    scores["accept"] += max(-0.2, min(0.2, (trust - 0.5) * 0.4))
    if not resources_ok:
        scores["rest"] += 0.35
        scores["accept"] -= 0.2
    if proposal.strip().lower() in {"", "none"}:
        scores["reject"] += 0.2
    choice = max(scores, key=scores.get)
    return {
        "proposal": proposal,
        "choice": choice,
        "options": scores,
        "archetype": None if preset is None else preset.key,
        "archetype_name": None if preset is None else preset.name_es,
        "resources_ok": resources_ok,
        "trust": trust,
        "policy_version": POLICY_VERSION,
        "note": "character_decision_only",
    }
