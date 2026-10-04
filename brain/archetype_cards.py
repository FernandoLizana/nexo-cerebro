"""22 Jungian symbols the agent can encounter, touch, and internalize.

Curiosity-and-learning cards. Design metaphor for exploration, not divination
and not a personality test. ``self`` and ``anima`` match the archetype keys
already used for Nexus and Nira in ``personality_archetypes``.

Read alias: saved state used meta["tarot"], kind "tarot", world["tarot"]
stats, event type "tarot_touch", event field "arcana_key", and object ids
prefixed with "arcana-". Those still resolve. Writes use archetype_card.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any


# Read alias: keys written before the Jungian rename of this deck.
LEGACY_META_KEY = "tarot"
LEGACY_KIND = "tarot"
LEGACY_STATS_KEY = "tarot"
LEGACY_TOUCH_EVENT = "tarot_touch"
LEGACY_SYMBOL_FIELD = "arcana_key"
LEGACY_ID_PREFIX = "arcana-"

TOUCH_EVENT = "archetype_card_touch"


@dataclass(frozen=True)
class ArchetypeCard:
    id: int
    key: str
    name_es: str
    concept: str
    meaning: str
    themes: tuple[str, ...]
    valence: float
    arousal: float
    drive_bias: dict[str, float] = field(default_factory=dict)

    @property
    def tags(self) -> list[str]:
        return [
            "archetype_card",
            f"symbol:{self.key}",
            f"concept:{self.concept}",
            *self.themes[:3],
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name_es": self.name_es,
            "concept": self.concept,
            "meaning": self.meaning,
            "themes": list(self.themes),
            "valence": self.valence,
            "arousal": self.arousal,
            "drive_bias": dict(self.drive_bias),
        }


# Numeric profile (valence, arousal, drive_bias) follows the previous deck
# so curiosity and affect keep the same shape. Names are Jung's vocabulary.
ARCHETYPE_CARDS: tuple[ArchetypeCard, ...] = (
    ArchetypeCard(0, "puer", "El Niño eterno", "inicio",
                  "Apertura sin forma previa: el comienzo como potencial.",
                  ("inicio", "apertura", "impulso"), 0.35, 0.72, {"seek_stimulus": 0.35}),
    ArchetypeCard(1, "trickster", "El Trickster", "transformación",
                  "Astucia que nombra y desarma el marco habitual.",
                  ("transformación", "astucia", "foco"), 0.42, 0.58, {"seek_stimulus": 0.2}),
    ArchetypeCard(2, "anima", "El Ánima", "intuición",
                  "Figura receptiva: umbral, imagen interior, memoria.",
                  ("intuición", "silencio", "memoria"), 0.12, 0.45, {"seek_rest": 0.15}),
    ArchetypeCard(3, "great_mother", "La Gran Madre", "vida",
                  "Nutrición, cuidado y abundancia vital.",
                  ("vida", "nutrición", "cuidado"), 0.55, 0.48, {"seek_food": 0.12}),
    ArchetypeCard(4, "senex", "El Senex", "orden",
                  "Límite, estructura y ley del hogar interior.",
                  ("orden", "protección", "disciplina"), 0.18, 0.42, {}),
    ArchetypeCard(5, "persona", "La Persona", "máscara",
                  "Rol social, enseñanza y pertenencia.",
                  ("máscara", "aprendizaje", "norma"), 0.22, 0.38, {}),
    ArchetypeCard(6, "syzygy", "La Sizigia", "vínculo",
                  "Pareja ánima-ánimus: elección entre caminos.",
                  ("vínculo", "elección", "pareja"), 0.48, 0.55, {"seek_stimulus": 0.1}),
    ArchetypeCard(7, "hero", "El Héroe", "voluntad",
                  "Avance consciente y cruce del impulso.",
                  ("voluntad", "viaje", "conflicto"), 0.28, 0.62, {"seek_stimulus": 0.25}),
    ArchetypeCard(8, "self", "El Sí-mismo", "centro",
                  "Centro que ordena opuestos: causa, efecto, discernimiento.",
                  ("centro", "discernimiento", "verdad"), 0.05, 0.4, {}),
    ArchetypeCard(9, "wise_old_man", "El Viejo sabio", "introspección",
                  "Soledad fecunda y pausa que discrimina.",
                  ("soledad", "sabiduría", "pausa"), 0.08, 0.32, {"seek_rest": 0.28}),
    ArchetypeCard(10, "enantiodromia", "La Enantiodromía", "ciclo",
                  "Lo extremo se vuelve su contrario.",
                  ("ciclo", "reversión", "cambio"), 0.15, 0.52, {}),
    ArchetypeCard(11, "animus", "El Ánimus", "coraje",
                  "Fuerza que domestica el instinto sin aplastarlo.",
                  ("coraje", "paciencia", "instinto"), 0.38, 0.44, {}),
    ArchetypeCard(12, "nekyia", "La Nekyia", "descenso",
                  "Viaje nocturno: espera, otro ángulo, entrega.",
                  ("descenso", "suspensión", "perspectiva"), -0.05, 0.36, {"seek_rest": 0.18}),
    ArchetypeCard(13, "rebirth", "El Renacimiento", "renacimiento",
                  "Fin de una forma y transformación, no aniquilación.",
                  ("renacimiento", "transformación", "cierre"), -0.22, 0.68, {}),
    ArchetypeCard(14, "transcendent_function", "La Función trascendente", "equilibrio",
                  "Mediación entre opuestos: mesura y reparación lenta.",
                  ("equilibrio", "mediación", "mesura"), 0.32, 0.35, {}),
    ArchetypeCard(15, "shadow", "La Sombra", "sombra",
                  "Lo no reconocido: deseo, dependencia, atadura.",
                  ("sombra", "atadura", "deseo"), -0.35, 0.62, {"seek_stimulus": 0.3}),
    ArchetypeCard(16, "inflation", "La Inflación", "crisis",
                  "Quiebre de una imagen demasiado grande de sí.",
                  ("crisis", "quiebre", "revelación"), -0.55, 0.82, {}),
    ArchetypeCard(17, "mandala", "El Mandala", "guía",
                  "Imagen de orden después del daño: guía tenue.",
                  ("guía", "orden", "calma"), 0.52, 0.38, {}),
    ArchetypeCard(18, "collective_unconscious", "El Inconsciente colectivo", "inconsciente",
                  "Fondo compartido: miedo, lo no dicho, poca luz.",
                  ("inconsciente", "miedo", "imagen"), -0.28, 0.58, {}),
    ArchetypeCard(19, "ego", "El Ego", "vitalidad",
                  "Claridad consciente, alegría y fuerza disponible.",
                  ("vitalidad", "alegría", "claridad"), 0.62, 0.55, {}),
    ArchetypeCard(20, "individuation", "La Individuación", "despertar",
                  "Llamado a integrar lo que aún estaba aparte.",
                  ("individuación", "despertar", "integración"), 0.35, 0.65, {}),
    ArchetypeCard(21, "coniunctio", "La Coniunctio", "totalidad",
                  "Unión de opuestos: ciclo cumplido, hogar en el todo.",
                  ("totalidad", "unión", "cierre"), 0.45, 0.48, {}),
)

_BY_KEY = {card.key: card for card in ARCHETYPE_CARDS}
_BY_ID = {card.id: card for card in ARCHETYPE_CARDS}

# Previous deck keys → current symbols. Read alias for saved object ids.
_LEGACY_CARD_KEYS: dict[str, str] = {
    "fool": "puer",
    "magician": "trickster",
    "priestess": "anima",
    "empress": "great_mother",
    "emperor": "senex",
    "hierophant": "persona",
    "lovers": "syzygy",
    "chariot": "hero",
    "justice": "self",
    "hermit": "wise_old_man",
    "wheel": "enantiodromia",
    "strength": "animus",
    "hanged": "nekyia",
    "death": "rebirth",
    "temperance": "transcendent_function",
    "devil": "shadow",
    "tower": "inflation",
    "star": "mandala",
    "moon": "collective_unconscious",
    "sun": "ego",
    "judgement": "individuation",
    "world": "coniunctio",
}


def resolve_card_key(name: str | None) -> str:
    raw = str(name or "").strip().lower()
    if raw in _BY_KEY:
        return raw
    return _LEGACY_CARD_KEYS.get(raw, raw)


def all_cards() -> list[ArchetypeCard]:
    return list(ARCHETYPE_CARDS)


def get_card(key_or_id: str | int) -> ArchetypeCard | None:
    if isinstance(key_or_id, int):
        return _BY_ID.get(key_or_id)
    raw = str(key_or_id).lower().strip()
    if raw.isdigit():
        return _BY_ID.get(int(raw))
    return _BY_KEY.get(resolve_card_key(raw))


def draw_card(*, exclude: set[str] | None = None) -> ArchetypeCard:
    pool = [card for card in ARCHETYPE_CARDS if not exclude or card.key not in exclude]
    return random.choice(pool or list(ARCHETYPE_CARDS))


def object_id_for(key: str) -> str:
    return f"symbol-{resolve_card_key(key)}"


def legacy_object_ids(key: str) -> set[str]:
    """Ids that already stand for this symbol, including the old prefix."""
    resolved = resolve_card_key(key)
    found = {object_id_for(resolved)}
    for old, new in _LEGACY_CARD_KEYS.items():
        if new == resolved:
            found.add(f"{LEGACY_ID_PREFIX}{old}")
    return found


def card_from_object(obj_id: str, label: str = "") -> ArchetypeCard | None:
    low = str(obj_id or "").lower()
    for prefix in ("symbol-", LEGACY_ID_PREFIX):
        if low.startswith(prefix):
            return get_card(low[len(prefix):])
    label_l = (label or "").lower()
    for card in ARCHETYPE_CARDS:
        if card.name_es.lower() in label_l:
            return card
    return None


def is_touch_event(event_type: str) -> bool:
    return event_type in (TOUCH_EVENT, LEGACY_TOUCH_EVENT)


def card_key_from_meta(meta: dict | None) -> str:
    meta = meta or {}
    raw = meta.get("archetype_card")
    if not raw:
        raw = meta.get(LEGACY_META_KEY)
    if not raw:
        return ""
    resolved = resolve_card_key(str(raw))
    return resolved if resolved in _BY_KEY else str(raw)


def is_archetype_card_meta(meta: dict | None) -> bool:
    meta = meta or {}
    if meta.get("archetype_card") or meta.get(LEGACY_META_KEY):
        return True
    return meta.get("kind") in ("archetype_card", LEGACY_KIND)


def normalize_card_meta(meta: dict | None) -> dict[str, Any]:
    """Copy the legacy meta key onto archetype_card and drop it."""
    out = dict(meta or {})
    legacy = out.pop(LEGACY_META_KEY, None)
    if legacy and not out.get("archetype_card"):
        out["archetype_card"] = legacy
    if out.get("archetype_card"):
        resolved = resolve_card_key(str(out["archetype_card"]))
        if resolved in _BY_KEY:
            out["archetype_card"] = resolved
    if out.get("kind") == LEGACY_KIND:
        out["kind"] = "archetype_card"
    return out


def legacy_stats(world_data: dict | None) -> dict | None:
    """Accept card-stat blocks from current or older world snapshots.

    The numbers are recomputed from objects. A present legacy key must not raise.
    """
    if not isinstance(world_data, dict):
        return None
    stats = world_data.get("archetype_cards")
    if stats is None:
        stats = world_data.get(LEGACY_STATS_KEY)
    if isinstance(stats, dict):
        return stats
    return None


def experience_text(card: ArchetypeCard) -> str:
    return (
        f"Símbolo jungiano: {card.name_es}. Concepto: {card.concept}. "
        f"{card.meaning} Temas: {', '.join(card.themes)}."
    )


def apply_drive_bias(drives: dict[str, float], card: ArchetypeCard) -> dict[str, float]:
    out = dict(drives)
    for key, delta in card.drive_bias.items():
        out[key] = float(min(1.0, out.get(key, 0) + delta))
    return out


def recall_query(card: ArchetypeCard) -> str:
    return f"{card.name_es} {card.concept} {' '.join(card.themes)} {card.meaning[:80]}"


def reading_with_memories(card: ArchetypeCard, memories: list[dict]) -> str:
    base = experience_text(card)
    if not memories:
        return base
    echoes: list[str] = []
    for mem in memories[:3]:
        label = (mem.get("label") or "?").strip()
        room = mem.get("room") or ""
        if room:
            echoes.append(f"«{label}» (en {room})")
        else:
            echoes.append(f"«{label}»")
    echo_txt = "; ".join(echoes)
    return (
        f"{base} En la memoria resurgen ecos: {echo_txt}. "
        f"El símbolo {card.name_es} dialoga con lo ya vivido."
    )
