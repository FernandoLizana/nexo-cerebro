"""
RAG de frases aprendidas del tutor — recuperación y adaptación para producción (Broca).

El tutor enseña; Nexo recuerda; al hablar adapta el ejemplo al estado corporal actual.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .caregiver_dialogue import is_fragmentary_speech, reply_engages_caregiver
from .verbalize import humanize_feeling

if TYPE_CHECKING:
    from .language_cortex import LanguageContext
    from .mind import InfantApeBrain

_LABEL_RE = re.compile(
    r"^cuidador:\s*(.+?)\s*\|\s*nexo aprendió:\s*(.+)$",
    re.I | re.DOTALL,
)


def tutor_memory_label(*, user_message: str, exemplar: str) -> str:
    u = (user_message or "").strip()[:60]
    e = (exemplar or "").strip()[:120]
    return f"cuidador: {u} | nexo aprendió: {e}"


def parse_tutor_label(label: str) -> tuple[str, str]:
    raw = (label or "").strip()
    m = _LABEL_RE.match(raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if raw.lower().startswith("aprendizaje:"):
        rest = raw.split(":", 1)[1].strip()
        return "", rest
    return "", raw


def extract_exemplar(mem: dict) -> str:
    _, exemplar = parse_tutor_label(mem.get("label", ""))
    return exemplar


def retrieve_learned_exemplars(
    brain: InfantApeBrain,
    user_message: str,
    *,
    k: int = 2,
    threshold: float = 0.50,
) -> list[dict]:
    return brain.memory_store.search_language_tutor(
        user_message, k=k, threshold=threshold
    )


def adapt_learned_exemplar(
    exemplar: str,
    user_message: str,
    ctx: LanguageContext,
) -> str | None:
    """Adapta frase aprendida al turno actual — no copia al tutor en crudo sin contexto."""
    text = (exemplar or "").strip()
    if not text or is_fragmentary_speech(text):
        return None

    feel = humanize_feeling(ctx.feelings[0]["signal"]) if ctx.feelings else "estoy bien"
    room = ctx.room or "casa"

    if reply_engages_caregiver(user_message, text):
        low = text.lower()
        feel_key = feel.split()[-1] if feel else ""
        if feel_key and feel_key not in low and len(text) < 160:
            return text.rstrip(".!? ") + f". {feel.capitalize()}, en {room}."
        return text

    short = user_message if len(user_message) <= 48 else user_message[:45] + "…"
    return (
        f"Te escucho: «{short}». "
        f"{text.rstrip('.')} "
        f"Ahora {feel}, en {room}."
    )
