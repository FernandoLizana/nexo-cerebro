"""
Convierte etiquetas internas (dormir@casa@422) en lenguaje hablable.
"""

from __future__ import annotations

import re

ROOM_NAMES: dict[str, str] = {
    "casa": "casa",
    "escritorio": "el escritorio",
    "sala_tv": "la sala",
    "bano": "el baño",
    "baño": "el baño",
    "jardin": "el jardín",
    "cocina": "la cocina",
}

RECALL_PHRASES: dict[str, str] = {
    "dormir": "cuando quise dormir",
    "comer": "cuando comí",
    "beber": "cuando bebí",
    "deambular": "cuando deambulé",
    "descansar": "cuando descansé",
    "estimularse (tv)": "cuando quise ver la tele",
    "estimularse (TV)": "cuando quise ver la tele",
    "buscar en la web": "cuando busqué en internet",
    "estudiar neurociencia": "cuando estudié",
    "acercarse a nira": "cuando me acerqué a ti",
    "acercarse a Nira": "cuando me acerqué a ti",
    "higiene": "cuando me cuidé",
    "baño": "cuando fui al baño",
    "atender dolor": "cuando me dolía el cuerpo",
    "buscar calor": "cuando busqué calor",
}


def _room_phrase(room: str) -> str:
    r = (room or "casa").strip().lower()
    if r == "casa":
        return "en casa"
    name = ROOM_NAMES.get(r, f"en {r.replace('_', ' ')}")
    if name.startswith("en "):
        return name
    return f"en {name}"


def _single_token_label(action: str, room: str, *, recall: bool) -> str:
    act = (action or "").strip()
    if not act:
        return ""
    loc = _room_phrase(room)
    key = act.lower()
    if recall:
        stem = RECALL_PHRASES.get(act) or RECALL_PHRASES.get(key) or f"lo de {act}"
        if loc == "en casa":
            return stem if stem.endswith("casa") else f"{stem} {loc}"
        return f"{stem} {loc}"
    if loc == "en casa":
        return f"{act} en casa"
    return f"{act} {loc}"


def humanize_memory_label(text: str, *, recall: bool = True) -> str:
    """Etiqueta técnica → frase natural para hablar o mostrar."""
    raw = (text or "").strip()
    if not raw:
        return ""
    if "@" not in raw:
        low = raw.lower()
        if low.startswith("imaginación:") or low.startswith("imaginacion:"):
            inner = raw.split(":", 1)[1].strip()
            if "@" in inner:
                parts = re.split(r"\s*[·•]\s*", inner)
                bits = [humanize_memory_label(p, recall=recall) for p in parts if p.strip()]
                joined = " y ".join(b for b in bits if b)
                return f"imaginar {joined}" if joined else "algo que imaginé"
        return raw

    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        if prefix.strip().lower() in ("imaginación", "imaginacion"):
            parts = re.split(r"\s*[·•]\s*", rest.strip())
            bits = [humanize_memory_label(p, recall=recall) for p in parts if p.strip()]
            joined = " y ".join(b for b in bits if b)
            return joined or "algo que imaginé"

    parts = raw.split("@")
    action = parts[0]
    room = parts[1] if len(parts) > 1 else "casa"
    return _single_token_label(action, room, recall=recall)


def format_episode_label(choice: str, room: str) -> str:
    """Etiqueta legible para almacenar en hipocampo (no técnica)."""
    return humanize_memory_label(f"{choice}@{room}@0", recall=False)


_PAIN_REGIONS: dict[str, str] = {
    "pecho": "el pecho",
    "cabeza": "la cabeza",
    "extremidades": "las extremidades",
}

_FEELING_PHRASES: dict[str, str] = {
    "hambre": "tengo hambre",
    "sed": "tengo sed",
    "frío": "tengo frío",
    "frio": "tengo frío",
    "calor": "tengo calor",
    "fatiga": "estoy cansado",
    "confort": "estoy a gusto",
    "temperatura": "noto el ambiente",
    "vejiga": "tengo ganas de ir al baño",
    "ganas de baño": "tengo ganas de ir al baño",
    "higiene": "me gustaría asearme",
    "malestar general": "me siento mal",
    "placer corporal": "me siento bien",
    "saciedad": "estoy lleno",
    "placer": "siento placer",
    "satisfacción": "me siento satisfecho",
    "satisfaccion": "me siento satisfecho",
    "antojo": "tengo antojo",
    "cansancio profundo": "estoy muy cansado",
    "bienestar": "me siento bien",
    "relajación": "estoy relajado",
    "relajacion": "estoy relajado",
    "bien": "estoy bien",
}

_VISIBLE_ARTICLES: dict[str, str] = {
    "cama": "la cama",
    "tele": "la tele",
    "tv": "la tele",
    "mesa": "la mesa",
    "silla": "la silla",
    "ventana": "la ventana",
    "puerta": "la puerta",
    "cocina": "la cocina",
    "jardín": "el jardín",
    "jardin": "el jardín",
    "baño": "el baño",
    "bano": "el baño",
    "escritorio": "el escritorio",
    "nira": "Nira",
    "companion": "Nira",
}


def humanize_feeling(signal: str) -> str:
    """Señal interoceptiva → frase hablable en primera persona."""
    s = (signal or "").strip().lower()
    if not s:
        return "estoy bien"
    if s.startswith("dolor "):
        region = s[6:].strip()
        body = _PAIN_REGIONS.get(region, region)
        return f"me duele {body}"
    return _FEELING_PHRASES.get(s, f"siento {signal}")


def humanize_visible(label: str) -> str:
    """Etiqueta de objeto → grupo nominal natural."""
    s = (label or "").strip()
    if not s:
        return "lo de alrededor"
    key = s.lower()
    if key in _VISIBLE_ARTICLES:
        return _VISIBLE_ARTICLES[key]
    if re.match(r"^(el|la|los|las)\s", key):
        return s
    return f"lo de {s.replace('_', ' ')}"
