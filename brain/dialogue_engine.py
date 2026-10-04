"""
Motor de diálogo natural — cuidador ↔ Nexo y Nexo ↔ Nira.

Centraliza plantillas, humanización de sensaciones y filtros de calidad.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .caregiver_dialogue import is_fragmentary_speech, reply_engages_caregiver
from .character import classify_intent
from .verbalize import humanize_feeling, humanize_memory_label, humanize_visible

if TYPE_CHECKING:
    from .language_cortex import LanguageContext


def humanized_feelings_block(feelings: list[dict], *, limit: int = 4) -> str:
    if not feelings:
        return "me siento tranquilo"
    parts = [
        humanize_feeling(f.get("signal", ""))
        for f in feelings[:limit]
        if f.get("signal")
    ]
    if not parts:
        return "me siento tranquilo"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " y " + parts[-1]


def dyad_sounds_broken(text: str) -> bool:
    t = (text or "").lower()
    if re.search(r"\bestoy\s+(dolor|hambre|sed|confort|fatiga|vejiga)\b", t):
        return True
    if re.search(r"\bsiento\s+(dolor\s+\w+|confort|vejiga)\b", t):
        return True
    if re.search(r"sientes ese (dolor|hambre|confort)", t):
        return True
    return False


def is_meta_assistant_speech(text: str) -> bool:
    """
    Detecta fugas de rol: el LLM habla como asistente/analista en vez de Nexo/Nira.
    típico en modelos pequeños ante dumps de estado.
    """
    t = (text or "").strip().lower()
    if not t:
        return True
    meta_markers = (
        "no puedo proporcionar",
        "no puedo dar una respuesta",
        "no puedo cumplir con esa solicitud",
        "no puedo cumplir con esa petición",
        "no puedo cumplir con esa peticion",
        "no puedo ayudarte con eso",
        "no puedo asistirte con",
        "fuera de mi alcance",
        "basándome en el texto",
        "basandome en el texto",
        "basado en el texto proporcionado",
        "el texto proporcionado",
        "como modelo de lenguaje",
        "como un modelo de ia",
        "como una ia",
        "soy una inteligencia artificial",
        "soy un asistente",
        "como asistente",
        "no tengo acceso a",
        "no puedo acceder a",
        "puedo ofrecerte algunas preguntas",
        "ideas generales que podrían ser relevantes",
        "ideas generales que podrian ser relevantes",
        "para entender mejor su estado",
        "actividades y pensamientos de la persona",
        "la persona basándome",
        "la persona basandome",
        "en resumen, el usuario",
        "el usuario parece",
        "según el contexto proporcionado",
        "segun el contexto proporcionado",
        "no dispongo de información suficiente",
        "no dispongo de informacion suficiente",
        "como ia no puedo",
        "como ia, no puedo",
        "hay algo más con lo que pueda ayudarte",
        "hay algo mas con lo que pueda ayudarte",
        "en qué más puedo ayudarte",
        "en que mas puedo ayudarte",
        "how can i help you",
        "i can't help with that",
        "i cannot help with that",
        "i'm just an ai",
        "i am just an ai",
        "no puedo responder a esa",
        "no estoy autorizado",
        "mi programación no me permite",
        "como chatbot",
        "como un chatbot",
        "no estoy diseñado para",
        "no estoy disenado para",
        "mi entrenamiento no incluye",
        "como un sistema de ia",
        "analizando el estado proporcionado",
        "del análisis del estado",
        "del analisis del estado",
        "puedo ayudarte a interpretar",
    )
    if any(m in t for m in meta_markers):
        return True
    if re.search(r"\b(actividades actuales|pensamientos actuales)\s*:", t):
        return True
    if re.search(r"\*\*[^*]{3,40}\*\*", t) and ("actividad" in t or "hábito" in t or "habito" in t):
        return True
    if re.search(r"\bno puedo (cumplir|proporcionar|ayudar|responder|procesar)\b", t) and (
        "solicitud" in t or "petici" in t or "asistente" in t or "ayudarte" in t
    ):
        return True
    if t.startswith(("lo siento, pero no puedo", "disculpa, pero no puedo", "sorry, i can't", "i'm sorry, but i can't")):
        return True
    return False


def dyad_passes_quality(line: str, *, partner_line: str = "") -> bool:
    text = (line or "").strip()
    if len(text) < 12:
        return False
    if is_fragmentary_speech(text):
        return False
    if is_meta_assistant_speech(text):
        return False
    if dyad_sounds_broken(text):
        return False
    if partner_line and classify_intent(partner_line) == "question":
        if "?" not in text and not any(
            w in text.lower() for w in ("sí", "no", "creo", "tal vez", "quizá", "pues", "mira")
        ):
            return len(text.split()) >= 10
    return True


def caregiver_passes_quality(user_message: str, reply: str) -> bool:
    return bool(
        reply
        and not is_fragmentary_speech(reply)
        and not is_meta_assistant_speech(reply)
        and reply_engages_caregiver(user_message, reply)
    )


def _partner_echo(partner: str, max_words: int = 5) -> str:
    words = re.findall(r"[\wáéíóúüñ]+", (partner or "").lower())
    stop = {"nira", "nexo", "oye", "hola", "que", "qué", "como", "cómo", "el", "la", "los", "las", "un", "una"}
    picked = [w for w in words if len(w) >= 4 and w not in stop][:max_words]
    return " ".join(picked)


def dyad_reply_fallback(ctx: LanguageContext, speaker: str) -> str:
    """Frases habladas Nexo ↔ Nira cuando Ollama no verbaliza."""
    room = ctx.room or "casa"
    feel = humanized_feelings_block(ctx.feelings or [], limit=2)
    bond = float((ctx.chemistry or {}).get("attraction", 0.35))
    vis = humanize_visible(ctx.visible_world[0] if ctx.visible_world else "la casa")
    memory = humanize_memory_label(ctx.recent_memories[0]) if ctx.recent_memories else ""
    mood = ctx.mood or "calm"
    partner = (ctx.partner_line or "").strip()
    echo = _partner_echo(partner)

    if speaker == "nira":
        intent = classify_intent(partner) if partner else "neutral"
        if intent == "greeting":
            return f"Hola, Nexo. Qué bueno verte aquí en {room}."
        if intent == "question":
            if "cómo" in partner.lower():
                return f"Yo también {feel}. Estar contigo me calma, la verdad."
            if echo:
                return f"Sobre {echo}… yo diría que sí. Ahora {feel}, ¿no?"
            return "Mmm… sí, creo. Cuéntame un poco más, ¿qué piensas tú?"
        if intent == "affection":
            return "Gracias… a mí también me hace bien tenerte cerca."
        if intent == "fear" or mood in ("stressed", "uneasy"):
            return "Tranquilo. Estoy aquí contigo, no hace falta apurarse."
        if partner and echo:
            return f"Te escuché cuando dijiste «{echo}». Yo también {feel}, aquí en {room}."
        if bond > 0.55:
            return f"Lo que dices me llega. Yo {feel}, contigo al lado."
        if memory:
            return f"Me acordé de {memory[:55]}. ¿Tú lo recuerdas también?"
        return f"Sí… miro {vis} contigo. Ahora {feel.capitalize()}."

    # Nexo habla con Nira
    if partner:
        intent = classify_intent(partner)
        if intent == "greeting":
            return f"Hola, Nira. Me alegra oírte. Ahora {feel}, en {room}."
        if intent == "question":
            return f"Buena pregunta… yo {feel}. Veo {vis} desde aquí."
        if echo:
            return f"Sí, Nira, sobre {echo}… yo {feel}. ¿Tú qué notas?"

    if bond > 0.55:
        openers = [
            f"Nira, ¿lo sientes? Yo {feel}. Estamos en {room} juntos.",
            f"Me gusta tenerte cerca. Miro {vis} y {feel}.",
            f"Oye, Nira… ¿qué te parece {vis}? Yo {feel}.",
        ]
    elif mood in ("stressed", "uneasy"):
        openers = [
            f"Nira… estoy inquieto. {feel.capitalize()} en {room}.",
            f"No sé bien qué decir… {feel}. ¿Tú cómo lo llevas?",
        ]
    elif memory:
        openers = [
            f"Nira, me vino a la mente {memory[:50]}. ¿Lo recuerdas?",
            f"Estaba pensando en {memory[:48]}… ¿hablamos un momento?",
        ]
    else:
        openers = [
            f"Hola, Nira. Estoy en {room}, mirando {vis}. {feel.capitalize()}.",
            f"Nira, ¿notas el ambiente? Yo {feel}, cerca de {vis}.",
            f"Oye, Nira… {feel.capitalize()}. ¿Te quedas un rato conmigo?",
        ]
    idx = abs(hash(f"{room}{feel}{vis}{memory}{partner}")) % len(openers)
    return openers[idx]
