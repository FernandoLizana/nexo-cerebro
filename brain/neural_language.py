"""
Corteza de lenguaje neuro-inspirada — sin LLM externo.

Modelo funcional (simplificado respecto al cerebro humano):
- Wernicke: intención + temas por reglas léxicas (sin inferencia pesada).
- Área premotora/Broca: composición desde consciencia, WM, afecto, metas y drives.
- Fascículo arqueado: ejemplos aprendidos del tutor (RAG) tienen prioridad en language_network.

Consumo: CPU mínimo, cero GPU, cero red (salvo CEREBRO_LANGUAGE=ollama).

Agency: solo verbaliza estado interno y progreso de estudio — nunca escribe choice_key
ni fuerza acciones motoras.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, replace

from .caregiver_dialogue import caregiver_reply_fallback, reply_engages_caregiver
from .character import classify_intent
from .dialogue_engine import dyad_reply_fallback, humanized_feelings_block
from .verbalize import humanize_feeling, humanize_memory_label, humanize_visible


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def resolve_language_backend() -> str:
    """
    neural (default) | ollama | off

    CEREBRO_LANGUAGE tiene prioridad. Si no está definido, CEREBRO_OLLAMA=1 activa ollama
    por compatibilidad con setups antiguos.
    """
    raw = os.environ.get("CEREBRO_LANGUAGE", "").strip().lower()
    if raw in ("ollama", "llm", "external"):
        return "ollama"
    if raw in ("off", "none", "silent", "0"):
        return "off"
    if raw in ("neural", "brain", "native", "internal"):
        return "neural"
    if raw and raw not in ("", "auto"):
        return "neural"
    if _env_bool("CEREBRO_OLLAMA", False):
        return "ollama"
    return "neural"


_CHOICE_PHRASES: dict[str, str] = {
    "wander": "deambular un poco",
    "explore": "explorar",
    "seek_water": "buscar agua",
    "seek_food": "comer",
    "sleep": "dormir",
    "rest": "descansar",
    "hygiene": "cuidarme",
    "study": "estudiar",
    "study_clinical": "repasar neurología clínica",
    "study_biopsych": "seguir biopsicología",
    "study_infant": "leer sobre el cerebro infantil",
    "tv": "ver la tele",
    "web": "buscar en internet",
    "social": "acercarme a Nira",
    "pain_relief": "aliviar el dolor",
    "desk": "sentarme en el escritorio",
}


_TOPIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("cuerpo", re.compile(r"\b(cuerpo|dolor|hambre|sed|fatiga|pecho|vejiga)\b", re.I)),
    ("cerebro", re.compile(r"\b(cerebro|neurona|memoria|sueño|sueñ|consciencia)\b", re.I)),
    ("emoción", re.compile(r"\b(miedo|triste|alegr|enojo|calma|estrés|estres)\b", re.I)),
    ("casa", re.compile(r"\b(casa|habitación|habitacion|cuarto|jardín|jardin)\b", re.I)),
    ("nira", re.compile(r"\bnira\b", re.I)),
    ("estudio", re.compile(r"\b(estudi|aprend|libro|leer|curso|manual|capítulo|capitulo)\b", re.I)),
    ("clínica", re.compile(r"\b(neurolog|acv|coma|glasgow|clínica|clinica|interno)\b", re.I)),
    ("biopsych", re.compile(r"\b(biopsicolog|neurotransmisor|dopamina|serotonin|limbic)\b", re.I)),
    ("infantil", re.compile(r"\b(infantil|bebé|bebe|desarrollo|apego|clementina)\b", re.I)),
]

_TRACK_SPEAK: dict[str, str] = {
    "curriculum": "el currículo de neurociencia",
    "brain_facts": "Brain Facts",
    "anatomy": "anatomía del cerebro",
    "clinical": "neurología clínica (Manual UDD)",
    "biopsych": "biopsicología",
    "infant": "el cerebro infantil",
    "library": "libros de la biblioteca",
}


def _study_tracks(ctx) -> dict:
    return ctx.study_tracks or {}


def _active_study_track(ctx) -> tuple[str, dict] | tuple[None, None]:
    """Track con foco reciente o más avance pendiente — solo lectura de estado."""
    tracks = _study_tracks(ctx)
    if not tracks:
        return None, None
    best_key: str | None = None
    best_score = -1.0
    for key, data in tracks.items():
        if not isinstance(data, dict):
            continue
        progress = float(data.get("progress") or 0)
        focus = int(data.get("focus_ticks") or 0)
        pending = 1.0 - progress if data.get("total", 0) else 0.0
        score = focus * 0.02 + pending * 0.5 + (0.15 if data.get("last_title") else 0.0)
        if score > best_score:
            best_score = score
            best_key = key
    if best_key is None:
        return None, None
    return best_key, tracks[best_key]


def _study_voice_line(ctx, *, prefer_current: bool = False) -> str:
    """Frase hablable sobre currículos — refleja memoria, no impone conducta."""
    key, data = _active_study_track(ctx)
    if not data:
        return ""
    label = _TRACK_SPEAK.get(key or "", key or "estudio")
    last = (data.get("last_title") or "").strip()
    current = (data.get("current_title") or "").strip()
    nxt = None
    for sec in data.get("sections") or []:
        if isinstance(sec, dict) and not sec.get("done"):
            nxt = sec.get("title")
            break
    progress = int(float(data.get("progress") or 0) * 100)

    if prefer_current and (current or nxt):
        title = current or nxt
        return f"En {label} estoy con «{title}» ({progress}% avanzado)"
    focus_ticks = int(data.get("focus_ticks") or 0)
    if last and focus_ticks > 0:
        return f"Todavía me ronda «{last}» del track de {label}"
    if last:
        return f"Lo último que estudié en {label} fue «{last}»"
    if nxt:
        return f"Me falta empezar «{nxt}» en {label}"
    if progress >= 100:
        return f"Ya recorrí todo el track de {label}"
    return f"Sigo aprendiendo {label} ({progress}%)"


def _study_thought_fragment(ctx) -> str:
    key, data = _active_study_track(ctx)
    if not data:
        return ""
    last = (data.get("last_title") or "").strip()
    if last:
        return last[:40]
    for sec in data.get("sections") or []:
        if isinstance(sec, dict) and sec.get("done") and sec.get("title"):
            return str(sec["title"])[:40]
    return ""


def _study_web_query(ctx) -> str | None:
    key, data = _active_study_track(ctx)
    if not data:
        return None
    last = (data.get("last_title") or "").strip()
    if key == "clinical" and last:
        return last[:45]
    if key == "biopsych":
        return "biopsicología cerebro conducta"
    if key == "infant":
        return "desarrollo cerebro infantil"
    if key == "brain_facts":
        return "brain facts neurociencia"
    if key == "anatomy":
        return "anatomía cerebral atlas"
    if key == "curriculum":
        return "neurociencia currículo"
    if key == "library":
        return "libros neurociencia"
    return None


def _extract_topics(text: str) -> list[str]:
    topics: list[str] = []
    for label, pat in _TOPIC_PATTERNS:
        if pat.search(text):
            topics.append(label)
    return topics[:3]


def _dominant_drive(ctx) -> tuple[str, float]:
    drives = ctx.drives or {}
    body = ctx.body or {}
    merged = dict(drives)
    for k in ("thirst", "hunger", "fatigue", "bladder", "pain"):
        v = body.get(k)
        if isinstance(v, (int, float)) and float(v) > 0.35:
            merged[f"seek_{k}" if k in ("thirst", "hunger") else k] = float(v)
    if not merged:
        return "", 0.0
    key, val = max(merged.items(), key=lambda x: float(x[1]))
    return str(key), float(val)


def _conscious_focus(ctx) -> str:
    con = ctx.consciousness or {}
    winner = con.get("winner") or {}
    label = (winner.get("label") or "").strip()
    if label:
        return humanize_memory_label(label, recall=False) or label
    narrative = (con.get("self") or {}).get("narrative") or []
    if narrative:
        return str(narrative[-1])[:60]
    return ""


def _wm_phrase(ctx) -> str:
    wm = ctx.working_memory or []
    if not wm:
        return ""
    top = wm[0]
    label = humanize_memory_label(top.get("label", ""), recall=True)
    return label[:70] if label else str(top.get("label", ""))[:70]


def _choice_phrase(ctx) -> str:
    pkt = ctx.thought_packet or {}
    ck = pkt.get("choice_key") or pkt.get("decision_key") or ctx.current_goal or ""
    ck = str(ck).strip().lower().replace(" ", "_")
    if ck in _CHOICE_PHRASES:
        return _CHOICE_PHRASES[ck]
    if ck.startswith("learned_"):
        return "seguir un hábito que aprendí"
    if ck:
        return ck.replace("_", " ")
    return ""


def _echo_keywords(text: str, *, max_words: int = 6) -> str:
    words = re.findall(r"[\wáéíóúüñ]+", (text or "").lower())
    stop = {
        "hola", "que", "qué", "como", "cómo", "el", "la", "los", "las", "un", "una",
        "de", "en", "y", "a", "me", "te", "se", "es", "por", "para", "dime", "diganme",
    }
    picked = [w for w in words if len(w) >= 4 and w not in stop][:max_words]
    return " ".join(picked)


@dataclass
class NeuralLanguageEngine:
    """Producción lingüística desde estado neural — sin llamadas HTTP."""

    source_tag: str = field(default="neural", init=False)

    def comprehend(self, user_message: str, ctx) -> dict:
        intent = classify_intent(user_message)
        topics = _extract_topics(user_message)
        return {"intent_hint": intent, "topics": topics, "source": "neural_wernicke"}

    def compose_world(self, ctx) -> tuple[str, str]:
        """Monólogo en voz alta desde estado corporal + consciencia."""
        feel = humanized_feelings_block(ctx.feelings or [], limit=2)
        room = ctx.room or "casa"
        focus = _conscious_focus(ctx)
        wm = _wm_phrase(ctx)
        choice = _choice_phrase(ctx)
        drive_key, drive_val = _dominant_drive(ctx)
        study = _study_voice_line(ctx)
        _, study_data = _active_study_track(ctx)

        if study and int((study_data or {}).get("focus_ticks") or 0) > 8:
            return f"{study}. {feel.capitalize()}, en {room}.", self.source_tag

        if drive_val > 0.62:
            if "water" in drive_key or drive_key == "thirst":
                return f"Tengo sed fuerte. Quiero agua, {feel}, aquí en {room}.", self.source_tag
            if "food" in drive_key or drive_key == "hunger":
                return f"Me apremia el hambre. Busco comer; ahora {feel}.", self.source_tag
            if drive_key in ("fatigue", "sleep"):
                return f"Me pesa el cansancio. Necesito descansar en {room}.", self.source_tag

        if ctx.companion_present and float((ctx.chemistry or {}).get("attraction", 0)) > 0.5:
            who = ctx.companion_name or "Nira"
            if choice:
                return (
                    f"Siento a {who} cerca mientras pienso en {choice}. {feel.capitalize()}.",
                    self.source_tag,
                )
            return f"{who} está cerca. {feel.capitalize()}, en {room}.", self.source_tag

        if focus and wm:
            return f"Ahora mismo {focus}. También recuerdo {wm}. {feel.capitalize()}.", self.source_tag
        if focus:
            if study:
                return f"Lo que más ocupa mi mente: {focus}. {study}. {feel.capitalize()}.", self.source_tag
            return f"Lo que más ocupa mi mente: {focus}. {feel.capitalize()}, en {room}.", self.source_tag
        if choice:
            vis = humanize_visible(ctx.visible_world[0]) if ctx.visible_world else room
            if study and choice.startswith(("repasar", "seguir", "leer")):
                return f"A veces pienso en {choice}. {study}. Miro {vis} y {feel}.", self.source_tag
            return f"Quiero {choice}. Miro {vis} y {feel}.", self.source_tag
        if study:
            return f"{study}. {feel.capitalize()}, en {room}.", self.source_tag
        if wm:
            return f"Tengo en la cabeza {wm}. {feel.capitalize()}.", self.source_tag
        if ctx.feelings:
            return f"{feel.capitalize()}. Estoy en {room}.", self.source_tag
        return f"Estoy aquí en {room}, en silencio.", self.source_tag

    def compose_chat(self, ctx) -> tuple[str, str]:
        """Diálogo con cuidador — reconoce turno + estado interno."""
        msg = (ctx.user_message or "").strip()
        intent = ctx.intent or classify_intent(msg)
        feel = humanized_feelings_block(ctx.feelings or [], limit=2)
        room = ctx.room or "casa"
        echo = _echo_keywords(msg)
        focus = _conscious_focus(ctx)
        wm = _wm_phrase(ctx)
        sky = " Esa voz desde arriba me envuelve." if ctx.caregiver_from_sky else ""
        topics = _extract_topics(msg)
        study = _study_voice_line(ctx, prefer_current="estudio" in topics or "cerebro" in topics)

        for exemplar in ctx.learned_exemplars or []:
            if exemplar and reply_engages_caregiver(msg, exemplar):
                low = exemplar.lower()
                if feel.split()[-1].lower() not in low and len(exemplar) < 180:
                    return exemplar.rstrip(".!? ") + f". {feel.capitalize()}, en {room}.", "learned"

        if intent == "greeting":
            return (
                f"Hola… me alegra oírte.{sky} {feel.capitalize()}, en {room}. ¿Cómo estás tú?",
                self.source_tag,
            )

        if intent == "question":
            if study and ("cerebro" in topics or "estudio" in topics or "clínica" in topics):
                return (
                    f"{study}.{sky} No lo domino del todo — {feel}. ¿Me ayudas a entenderlo?",
                    self.source_tag,
                )
            if re.search(r"\bcómo\s+est", msg.lower()):
                extra = f" En mi mente: {focus}." if focus else ""
                return f"Ahora {feel}.{extra} Estoy en {room}.{sky}", self.source_tag
            if echo:
                wm_bit = f" Recuerdo {wm}." if wm else ""
                return (
                    f"Sobre {echo}… no lo tengo del todo claro, pero {feel}.{wm_bit} ¿Me lo explicas?",
                    self.source_tag,
                )
            vis = ", ".join(ctx.visible_world[:2]) if ctx.visible_world else "poco alrededor"
            return (
                f"Buena pregunta.{sky} Veo {vis} y {feel}. ¿Qué querías saber exactamente?",
                self.source_tag,
            )

        if intent == "affection":
            bond = float((ctx.chemistry or {}).get("attraction", 0.35))
            if bond > 0.55:
                return f"Yo también… me hace bien oírte.{sky} {feel.capitalize()}.", self.source_tag
            return f"Gracias por decírmelo.{sky} {feel.capitalize()}, aquí en {room}.", self.source_tag

        if intent == "fear":
            return (
                f"Un poco asustado, sí.{sky} {feel.capitalize()}. ¿Puedes quedarte un momento?",
                self.source_tag,
            )

        if echo:
            choice = _choice_phrase(ctx)
            if choice:
                return (
                    f"Escuché lo de {echo}.{sky} Ahora pienso en {choice} y {feel}.",
                    self.source_tag,
                )
            return f"Te escucho sobre {echo}.{sky} {feel.capitalize()}, en {room}.", self.source_tag

        reply = caregiver_reply_fallback(
            user_message=msg,
            intent=intent,
            mood=ctx.mood,
            room=room,
            feelings=ctx.feelings,
            visible=ctx.visible_world,
            companion_name=ctx.companion_name,
            companion_present=ctx.companion_present,
            voice_from_sky=ctx.caregiver_from_sky,
            memory_label=ctx.memory_label,
            remembered=ctx.remembered,
        )
        return reply, self.source_tag

    def compose_feelings(self, ctx) -> tuple[str, str]:
        if not ctx.feelings:
            return "Sensaciones neutras.", self.source_tag
        parts = [humanize_feeling(f["signal"]) for f in ctx.feelings[:4] if f.get("signal")]
        mods = ctx.modulators or {}
        extras: list[str] = []
        if float(mods.get("oxytocin", 0)) > 0.55:
            extras.append("calor por dentro")
        if float(mods.get("cortisol", 0)) > 0.55:
            extras.append("nervios en el pecho")
        if float(mods.get("dopamine", 0)) > 0.6:
            extras.append("ganas de moverme")
        body = "Ahora " + ", ".join(parts) + "."
        if extras:
            body += " También siento " + " y ".join(extras) + "."
        return body, self.source_tag

    def compose_thought(self, ctx) -> tuple[str, str]:
        pkt = ctx.thought_packet or {}
        clarity = float(pkt.get("clarity", ctx.consciousness.get("metacognition", {}).get("clarity", 0.7)))
        parts: list[str] = []
        for f in (pkt.get("interoception") or ctx.feelings or [])[:2]:
            sig = f.get("signal", "")
            if sig:
                parts.append(humanize_feeling(sig).split()[-1])
        if pkt.get("scene_gist"):
            parts.append(str(pkt["scene_gist"])[:30])
        if float((pkt.get("pain") or {}).get("total", 0)) > 0.15:
            parts.append("duele")
        echo = pkt.get("memory_echo")
        if echo:
            parts.append(humanize_memory_label(str(echo))[:35])
        focus = _conscious_focus(ctx)
        if focus and focus not in parts:
            parts.append(focus[:35])
        study_bit = _study_thought_fragment(ctx)
        if study_bit and study_bit not in parts:
            parts.append(study_bit[:35])

        if clarity < 0.3:
            return "…" + (parts[0] if parts else ""), self.source_tag
        if parts:
            return "…" + "… ".join(parts[:3]) + "…", self.source_tag
        flow = ctx.thought_flow or []
        if flow:
            chunk = " · ".join(f.get("raw", "")[:22] for f in flow[-3:] if f.get("raw"))
            return f"…{chunk}…", self.source_tag
        return "…", self.source_tag

    def compose_web_query(self, ctx) -> tuple[str, str]:
        curated = _study_web_query(ctx)
        if curated:
            return curated, self.source_tag
        wm = _wm_phrase(ctx)
        focus = _conscious_focus(ctx)
        if "neuro" in (focus + wm).lower() or "estudi" in (focus + wm).lower():
            return "cerebro humano desarrollo", self.source_tag
        if ctx.recent_memories:
            q = humanize_memory_label(ctx.recent_memories[0])[:40]
            return q if q else "curiosidad cerebro", self.source_tag
        drive_key, drive_val = _dominant_drive(ctx)
        if drive_val > 0.5 and "pain" in drive_key:
            return "dolor cuerpo alivio", self.source_tag
        return "documentales naturaleza", self.source_tag

    def compose_youtube_query(self, ctx) -> tuple[str, str]:
        choice = _choice_phrase(ctx)
        if "estudi" in choice or "neuro" in choice:
            return "documental cerebro", self.source_tag
        if ctx.recent_memories:
            return humanize_memory_label(ctx.recent_memories[0])[:35], self.source_tag
        return "naturaleza relax", self.source_tag

    def compose_dyad(self, ctx, *, speaker: str = "nexo") -> tuple[str, str]:
        return dyad_reply_fallback(ctx, speaker), self.source_tag

    def compose_tutor_exemplar(self, user_message: str, ctx) -> str | None:
        """Frase ejemplo para aprendizaje — imita tutor sin LLM."""
        sub = replace(
            ctx,
            user_message=user_message,
            intent=classify_intent(user_message),
        )
        base, _ = self.compose_chat(sub)
        if not base or len(base) < 12:
            return None
        return base


_ENGINE = NeuralLanguageEngine()


def get_neural_language_engine() -> NeuralLanguageEngine:
    return _ENGINE
