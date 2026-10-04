"""
Respuestas de fallback cuando Ollama no verbaliza — diálogo coherente cuidador ↔ Nexo.
"""

from __future__ import annotations

import re
from typing import Any


_ELLIPSIS_RE = re.compile(r"\.{2,}|…")


def _normalize_ellipsis(text: str) -> str:
    return _ELLIPSIS_RE.sub("…", (text or "").strip())


def is_fragmentary_speech(text: str) -> bool:
    """Detecta salidas tipo «…hambre… cerca… calor…» en lugar de frases."""
    t = (text or "").strip()
    if not t:
        return True
    norm = _normalize_ellipsis(t)
    if norm.count("…") >= 2:
        return True
    if norm.startswith("…") and norm.endswith("…") and len(norm.split()) <= 8:
        return True
    if re.search(r"imaginaci[oó]n\s*:", t, re.I) and _ELLIPSIS_RE.search(t):
        return True
    chunks = [c.strip() for c in _ELLIPSIS_RE.split(t) if c.strip()]
    if len(chunks) >= 3 and len(t) < 120:
        if all(len(c.split()) <= 4 for c in chunks):
            return True
    return False


def reply_engages_caregiver(user_message: str, reply: str) -> bool:
    """True si la respuesta parece dirigida al cuidador, no un volcado interno."""
    user = (user_message or "").strip()
    resp = (reply or "").strip()
    if not user or not resp:
        return False
    if is_fragmentary_speech(resp):
        return False
    lower_r = resp.lower()
    if any(
        p in lower_r
        for p in (
            "te escucho",
            "oírte",
            "oirte",
            "gracias por",
            "perdona",
            "disculpa",
            "no lo tengo claro",
            "qué crees",
            "repíteme",
            "repetime",
            "hola",
            "adiós",
            "adios",
        )
    ):
        return True
    user_words = [
        w.strip("¿?!.,…")
        for w in re.findall(r"[\wáéíóúüñ]+", user.lower())
        if len(w) >= 4
    ]
    if user_words and any(w in lower_r for w in user_words):
        return True
    if "?" in resp and len(resp.split()) >= 5:
        return True
    if len(resp) >= 40 and resp.rstrip().endswith((".", "!", "?")):
        return True
    return len(resp.split()) >= 8 and not is_fragmentary_speech(resp)


def _feel_phrase(feelings: list[dict], mood: str) -> str:
    from .verbalize import humanize_feeling

    if feelings:
        f = feelings[0]
        sig = f.get("signal", "")
        inten = float(f.get("intensity", 0))
        if inten > 0.35 and sig:
            return humanize_feeling(sig).capitalize()
    if mood and mood not in ("calm", "neutral"):
        return f"Estoy {mood}"
    return "Estoy aquí, escuchando"


def _match_topic(lower: str) -> str | None:
    topics = [
        (r"\b(calor|caliente|abrigo|abrígate)\b", "calor"),
        (r"\b(fr[ií]o|frio|helad)\b", "frio"),
        (r"\b(hambre|comer|comida|cena|almuerzo)\b", "hambre"),
        (r"\b(sed|agua|beber)\b", "sed"),
        (r"\b(sueño|dormir|cama|descans)\b", "sueno"),
        (r"\b(miedo|asust|susto)\b", "miedo"),
        (r"\b(dolor|duele|herid)\b", "dolor"),
        (r"\b(triste|llor|pena)\b", "tristeza"),
        (r"\b(bien|content|feliz|alegr)\b", "bien"),
    ]
    for pat, key in topics:
        if re.search(pat, lower):
            return key
    return None


def caregiver_reply_fallback(
    *,
    user_message: str,
    intent: str = "neutral",
    mood: str = "calm",
    room: str = "",
    feelings: list[dict] | None = None,
    visible: list[str] | None = None,
    companion_name: str | None = None,
    companion_present: bool = False,
    voice_from_sky: bool = False,
    memory_label: str | None = None,
    remembered: bool = False,
) -> str:
    """Frases completas que reconocen al cuidador (sin «…hambre… cerca…»)."""
    msg = (user_message or "").strip()
    lower = msg.lower()
    room = room or "casa"
    feelings = feelings or []
    feel = _feel_phrase(feelings, mood)
    sky = " Esa voz desde arriba me envuelve." if voice_from_sky else ""

    topic = _match_topic(lower)

    if intent == "greeting" or re.search(r"\b(hola|buenas|hey|saludos)\b", lower):
        return f"Hola… me alegra oírte.{sky} {feel}, en {room}. ¿Cómo estás tú?"

    if re.search(r"\b(me gustar[ií]a|quisiera|podr[ií]as|ay[uú]dame)\b", lower):
        return (
            f"Te escucho.{sky} Me gustaría entender mejor… ahora {feel.lower()} en {room}. "
            f"¿Me lo explicas con calma?"
        )

    if intent == "farewell" or re.search(r"\b(adi[oó]s|chao|hasta luego)\b", lower):
        return f"Adiós… gracias por hablarme.{sky} Me quedo {mood} en {room}."

    if intent == "affection" or re.search(r"\b(quiero|amor|cariño|gracias|abrazo)\b", lower):
        return f"Yo también… me hace bien oírte.{sky} {feel}."

    if intent == "question" or "?" in msg:
        vis = ", ".join(visible[:3]) if visible else "poco alrededor"
        return (
            f"No lo tengo del todo claro… pero {feel.lower()} en {room}. "
            f"Veo {vis}. ¿Tú qué crees?"
        )

    if re.search(r"\b(no te entiendo|no entiendes|no me entiendes|no nos entendemos)\b", lower):
        return (
            f"Perdona… a veces me cuesta decirlo bien con palabras.{sky} "
            f"Ahora {feel.lower()} en {room}. ¿Puedes decírmelo otra vez, más despacio?"
        )

    if re.search(
        r"\b(qu[eé]\s+necesit|d[ií]ganme\s+qu[eé]|qu[eé]\s+precis|qu[eé]\s+quieres)\b",
        lower,
    ):
        from .verbalize import humanize_feeling

        needs: list[str] = []
        for f in feelings[:4]:
            sig = f.get("signal", "")
            if sig and float(f.get("intensity", 0)) > 0.25:
                needs.append(humanize_feeling(sig))
        if not needs:
            needs = [feel.lower()]
        need_txt = ", ".join(needs[:3])
        return (
            f"Te escucho.{sky} Ahora mismo {need_txt}, en {room}. "
            f"¿Tú puedes ayudarme con algo de eso?"
        )

    replies: dict[str, str] = {
        "calor": f"Sí, también siento calor… el aire en {room} pesa.{sky} {feel}.",
        "frio": f"Tengo frío… busco calor en {room}.{sky} {feel}.",
        "hambre": f"Tengo hambre… el estómago me pide comida.{sky} Estoy en {room}, {feel.lower()}.",
        "sed": f"Tengo sed… me gustaría beber algo.{sky} {feel}, en {room}.",
        "sueno": f"Me pesa el sueño… la cama me llama.{sky} {feel}.",
        "miedo": f"Algo me inquieta… pero oírte calma un poco.{sky} {feel}.",
        "dolor": f"Me duele el cuerpo… lo noto fuerte.{sky} {feel}, en {room}.",
        "tristeza": f"Me siento un poco triste… pero gracias por quedarte.{sky} {feel}.",
        "bien": f"Me alegra oírte… yo también estoy algo mejor.{sky} {feel}, en {room}.",
    }

    if topic and topic in replies:
        base = replies[topic]
        if remembered and memory_label:
            base += f" Me acordé de {memory_label[:32]}."
        return base

    if msg:
        short = msg if len(msg) <= 48 else msg[:45] + "…"
        extra = ""
        if companion_present and companion_name:
            extra = f" {companion_name} está cerca."
        if remembered and memory_label:
            extra += f" Recuerdo {memory_label[:28]}."
        return (
            f"Te escucho: «{short}».{sky}{extra} "
            f"Ahora {feel.lower()} en {room}."
        )

    return f"{feel}.{sky} Estoy en {room}."
