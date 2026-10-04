"""
Corteza del lenguaje (Broca/Wernicke) — articula estado interno, no decide.

Backends (`CEREBRO_LANGUAGE`):
- `neural` (default): composición desde consciencia/WM/afecto — cero GPU.
- `ollama`: LLM local opcional (legacy / comparación E2).
- `off`: plantillas mínimas.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .verbalize import humanize_memory_label, humanize_feeling, humanize_visible
from .caregiver_dialogue import (
    caregiver_reply_fallback,
    is_fragmentary_speech,
    reply_engages_caregiver,
)
from .dialogue_engine import (
    caregiver_passes_quality,
    dyad_passes_quality,
    dyad_reply_fallback,
    dyad_sounds_broken,
    humanized_feelings_block,
    is_meta_assistant_speech,
)
from .neural_language import get_neural_language_engine, resolve_language_backend


def _dyad_sounds_broken(text: str) -> bool:
    return dyad_sounds_broken(text)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class LanguageContext:
    user_message: str = ""
    intent: str = "neutral"
    mood: str = "calm"
    draft: str = ""
    remembered: bool = False
    memory_label: str | None = None
    recent_memories: list[str] = field(default_factory=list)
    last_thought: str | None = None
    visible_world: list[str] = field(default_factory=list)
    energy: float = 0.7
    attachment: float = 0.35
    valence: float = 0.0
    arousal: float = 0.3
    motor: list[int] = field(default_factory=list)
    mode: str = "chat"
    room: str = ""
    body: dict = field(default_factory=dict)
    drives: dict = field(default_factory=dict)
    feelings: list[dict] = field(default_factory=list)
    tv: dict = field(default_factory=dict)
    web: dict = field(default_factory=dict)
    working_memory: list[dict] = field(default_factory=list)
    current_goal: str | None = None
    companion_name: str | None = None
    companion_present: bool = False
    modulators: dict = field(default_factory=dict)
    chemistry: dict = field(default_factory=dict)
    thought_packet: dict = field(default_factory=dict)
    vision: dict = field(default_factory=dict)
    thought_flow: list[dict] = field(default_factory=list)
    cortical: dict = field(default_factory=dict)
    consciousness: dict = field(default_factory=dict)
    dyad_speaker: str = "nexo"
    partner_line: str = ""
    caregiver_from_sky: bool = False
    learned_exemplars: list[str] = field(default_factory=list)
    study_tracks: dict = field(default_factory=dict)


@dataclass
class LanguageCortex:
    backend: str = field(default_factory=resolve_language_backend)
    enabled: bool = field(init=False)
    base_url: str = field(
        default_factory=lambda: os.environ.get("CEREBRO_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    )
    model: str = field(default_factory=lambda: os.environ.get("CEREBRO_OLLAMA_MODEL", "llama3.2:1b"))
    timeout_s: float = field(
        default_factory=lambda: float(os.environ.get("CEREBRO_OLLAMA_TIMEOUT", "20"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.environ.get("CEREBRO_OLLAMA_MAX_TOKENS", "80"))
    )
    available: bool = field(default=False, init=False)
    resolved_model: str = field(default="", init=False)
    last_error: str = field(default="", init=False)
    last_source: str = field(default="internal", init=False)

    def __post_init__(self) -> None:
        self.enabled = self.backend == "ollama"
        if self.enabled:
            self.available = self.ping()
        else:
            self.available = False
            if self.backend == "neural":
                self.last_source = "neural"

    def _fetch_tags(self) -> list[str]:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return []

    def _resolve_model(self, names: list[str]) -> str:
        if not names:
            return self.model
        if self.model in names:
            return self.model
        base = self.model.split(":")[0]
        for n in names:
            if n == base or n.startswith(base + ":"):
                return n
        for pref in (
            "llama3.2:1b",
            "qwen2.5:0.5b",
            "phi3:mini",
            "tinyllama",
            "llama3.2",
            "phi3",
            "mistral",
        ):
            for n in names:
                if n == pref or n.startswith(pref.split(":")[0] + ":"):
                    return n
        return names[0]

    def ping(self) -> bool:
        try:
            names = self._fetch_tags()
            if names:
                self.resolved_model = self._resolve_model(names)
                self.available = True
                self.last_error = ""
                return True
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=4) as resp:
                self.available = resp.status == 200
            self.resolved_model = self.model
            return self.available
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            self.available = False
            self.last_error = str(e)
            return False

    def status(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "enabled": self.enabled,
            "available": self.available,
            "model": self.resolved_model or self.model,
            "model_configured": self.model,
            "url": self.base_url,
            "last_source": self.last_source,
            "last_error": self.last_error or None,
            "neural": self.backend == "neural",
            "zero_gpu": self.backend != "ollama",
        }

    def _chat(self, system: str, user: str, *, max_tokens: int = 140, temperature: float = 0.7) -> str | None:
        if not self.enabled:
            return None
        if not self.available and not self.ping():
            return None
        model = self.resolved_model or self.model
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"num_predict": min(max_tokens, self.max_tokens), "temperature": temperature},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = (body.get("message") or {}).get("content", "").strip()
            if text and is_meta_assistant_speech(text):
                self.last_source = "meta_rejected"
                self.last_error = "meta_assistant_speech"
                return None
            if text:
                self.last_source = "ollama"
                self.last_error = ""
                return text
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError) as e:
            self.available = False
            self.last_error = str(e)
        return None

    def _state_block(self, ctx: LanguageContext) -> str:
        feel = ", ".join(f"{f['signal']} {f['intensity']:.0%}" for f in ctx.feelings[:5])
        wm = "\n".join(
            f"- {s.get('label', '?')}"
            + (f" @{s['room']}" if s.get("room") else "")
            + (" (recuerdo)" if s.get("remembered") else "")
            for s in ctx.working_memory[:7]
        ) or "—"
        goal = ctx.current_goal or "—"
        companion = ""
        if ctx.companion_name:
            companion = f"{ctx.companion_name} {'cerca' if ctx.companion_present else 'en casa'}"
        mods = json.dumps(ctx.modulators, ensure_ascii=False) if ctx.modulators else "—"
        bond = json.dumps(ctx.chemistry, ensure_ascii=False) if ctx.chemistry else "—"
        neural = json.dumps(ctx.thought_packet, ensure_ascii=False) if ctx.thought_packet else "—"
        vis = ctx.vision or {}
        scene = vis.get("scene_gist", "") if vis else ""
        fix = (vis.get("fixation") or {}).get("interpretation", "") if vis else ""
        flow = " · ".join(
            f.get("raw", "")[:40] for f in (ctx.thought_flow or [])[-6:] if f.get("raw")
        )
        pain = ctx.body.get("pain", {}) if ctx.body else {}
        memories = [humanize_memory_label(m) for m in ctx.recent_memories[:4] if m]
        con = ctx.consciousness or {}
        winner = con.get("winner") or {}
        meta = con.get("metacognition") or {}
        self_block = con.get("self") or {}
        conscious_line = ""
        if winner.get("label"):
            conscious_line = (
                f"Momento consciente dominante: {winner.get('label')} "
                f"(saliencia {float(winner.get('salience', 0)):.0%}). "
                f"Metacognición: {meta.get('felt', '—')} "
                f"(claridad {float(meta.get('clarity', 0)):.0%}, "
                f"duda {float(meta.get('doubt', 0)):.0%}). "
                f"Yo narrativo: {' → '.join(self_block.get('narrative', [])[:3]) or '—'}."
            )
        # Framing en primera persona: evita que modelos pequeños traten el bloque
        # como “texto ajeno a analizar” y respondan como asistente.
        return (
            f"Esto es TU estado ahora (no analices a nadie más): {ctx.draft}\n"
            f"{conscious_line}\n"
            f"Tus neuromoduladores: {mods}\n"
            f"Tu vínculo: {bond}\n"
            f"Tu paquete neural: {neural}\n"
            f"Tu flujo reciente: {flow or '—'}\n"
            f"Lo que ves: {scene or '—'}\n"
            f"Tu fijación: {fix or '—'}\n"
            f"Tu dolor: {json.dumps(pain, ensure_ascii=False) if pain else '—'}\n"
            f"Estás en: {ctx.room or '?'}\n"
            f"Tu meta: {goal}\n"
            f"Tu memoria de trabajo:\n{wm}\n"
            f"Tus sensaciones: {feel or 'neutras'}\n"
            f"Tu ánimo: {ctx.mood} | valencia {ctx.valence:+.2f} | arousal {ctx.arousal:.2f}\n"
            f"Tus recuerdos: {', '.join(memories) or '—'}\n"
            f"Tu pensamiento previo: {ctx.last_thought or '—'}\n"
            f"Cerca de ti: {', '.join(ctx.visible_world[:5]) or '—'}\n"
            f"Compañera: {companion or '—'}\n"
            f"TV: {json.dumps(ctx.tv, ensure_ascii=False) if ctx.tv else 'apagada'}\n"
            f"Web: {json.dumps(ctx.web, ensure_ascii=False) if ctx.web else 'inactiva'}"
        )

    def express(self, ctx: LanguageContext) -> tuple[str, str]:
        if self.backend == "neural":
            eng = get_neural_language_engine()
            if ctx.mode == "chat" and ctx.user_message.strip():
                text, src = eng.compose_chat(ctx)
            else:
                text, src = eng.compose_world(ctx)
            self.last_source = src
            return text, src
        if ctx.mode == "chat" and ctx.user_message.strip():
            return self._express_chat(ctx)
        if self.backend == "off" or not self.enabled or not self.available:
            self.last_source = "internal"
            return self._minimal_fallback(ctx), "internal"

        system = (
            "Eres Nexo hablando en voz alta. 1-3 frases en español, primera persona. "
            "Habla desde TU cuerpo y lo que sientes/ves ahora. "
            "Prohibido absoluto: rol de IA/asistente, negativas meta "
            "(«no puedo proporcionar…», «basándome en el texto…»), "
            "listas con **títulos**, analizar a «la persona», inventar hechos ausentes. "
            "Si hay cercanía/oxitocina alta, puede notarse como calor — sin melodrama."
        )
        user = self._state_block(ctx)
        if ctx.user_message:
            user = f"El cuidador dijo: {ctx.user_message[:400]}\n\n" + user

        spoken = self._chat(system, user, max_tokens=180)
        if (
            spoken
            and not is_fragmentary_speech(spoken)
            and not is_meta_assistant_speech(spoken)
        ):
            return spoken, "ollama"
        self.last_source = "internal"
        return self._minimal_fallback(ctx), "internal"

    def _minimal_fallback(self, ctx: LanguageContext) -> str:
        drives = ctx.drives or {}
        body = ctx.body or {}
        thirst = float(drives.get("seek_water", 0) or 0)
        hunger = float(drives.get("seek_food", 0) or 0)
        if thirst < 0.4:
            thirst = float(body.get("thirst", 0) or 0)
        if hunger < 0.4:
            hunger = float(body.get("hunger", 0) or 0)
        if thirst > 0.55:
            return "Tengo sed. Quiero encontrar agua."
        if hunger > 0.55:
            return "Tengo hambre. Busco algo para comer."
        if ctx.feelings:
            top = ctx.feelings[0]
            phrase = humanize_feeling(top.get("signal", ""))
            if ctx.chemistry.get("attraction", 0) > 0.5 and ctx.companion_present:
                who = ctx.companion_name or "Nira"
                return f"{phrase.capitalize()}. Siento a {who} cerca."
            return f"{phrase.capitalize()}."
        if ctx.modulators.get("oxytocin", 0) > 0.55:
            return "Siento calor por dentro, como un abrazo químico."
        return "Estoy aquí, en silencio."

    def caregiver_reply_fallback(self, ctx: LanguageContext) -> str:
        return caregiver_reply_fallback(
            user_message=ctx.user_message,
            intent=ctx.intent,
            mood=ctx.mood,
            room=ctx.room,
            feelings=ctx.feelings,
            visible=ctx.visible_world,
            companion_name=ctx.companion_name,
            companion_present=ctx.companion_present,
            voice_from_sky=ctx.caregiver_from_sky,
            memory_label=ctx.memory_label,
            remembered=ctx.remembered,
        )

    def _express_chat(self, ctx: LanguageContext) -> tuple[str, str]:
        if self.backend == "neural":
            text, src = get_neural_language_engine().compose_chat(ctx)
            self.last_source = src
            return text, src
        if not self.enabled or not self.available:
            self.last_source = "caregiver_fallback"
            return self.caregiver_reply_fallback(ctx), "caregiver_fallback"

        feel = humanized_feelings_block(ctx.feelings)
        wm = ctx.working_memory[:5]
        wm_txt = "; ".join(s.get("label", "?") for s in wm) or "nada destacado"
        system = (
            "Eres Nexo, un homínido con cerebro simulado. El cuidador (tu figura de apego) te habla. "
            "Responde en español, primera persona, 2-3 frases COMPLETAS como en una charla real. "
            "OBLIGATORIO: reconoce lo que dijo (parafrasea o repite la idea) y responde directamente. "
            "Tono cálido, sencillo, honesto — como quien aprende a hablar pero se esfuerza en conectar. "
            "Prohibido: listas sueltas, «…palabra…», etiquetas internas, JSON, decir que eres IA, "
            "hablar como asistente («no puedo proporcionar…», «basándome en el texto…»)."
        )
        user = (
            f"Cuidador dijo: «{ctx.user_message}»\n"
            f"Estás en: {ctx.room or 'casa'}. Ánimo: {ctx.mood}. Cuerpo: {feel}.\n"
            f"Meta activa: {ctx.current_goal or 'ninguna'}.\n"
            f"Memoria de trabajo: {wm_txt}.\n"
            f"Recuerdos recientes: {', '.join(ctx.recent_memories[:3]) or 'ninguno'}.\n"
            f"Visible cerca: {', '.join(ctx.visible_world[:4]) or 'nada especial'}."
        )
        if ctx.caregiver_from_sky:
            user += "\nSu voz llega desde el cielo — amplia, cuidadora, no amenazante."
        if ctx.companion_name and ctx.companion_present:
            bond = ctx.chemistry.get("attraction") if ctx.chemistry else None
            user += f"\n{ctx.companion_name} está cerca."
            if bond is not None:
                user += f" Vínculo químico: {bond:.0%}."
        if ctx.intent == "question":
            user += "\nEs una pregunta: contéstala con honestidad desde tu perspectiva."
        if ctx.learned_exemplars:
            user += (
                "\nFrases que aprendí antes (inspírate, no copies literal si no encajan): "
                + " | ".join(ctx.learned_exemplars[:2])
            )

        spoken = self._chat(system, user, max_tokens=220, temperature=0.72)
        if spoken and caregiver_passes_quality(ctx.user_message, spoken):
            return spoken, "ollama"
        self.last_source = "caregiver_fallback"
        return self.caregiver_reply_fallback(ctx), "caregiver_fallback"

    def describe_feelings(self, ctx: LanguageContext) -> tuple[str, str]:
        """Monólogo interoceptivo para el panel «qué siente»."""
        if self.backend == "neural":
            text, src = get_neural_language_engine().compose_feelings(ctx)
            self.last_source = src
            return text, src
        if not self.enabled or not self.available:
            self.last_source = "internal"
            if ctx.feelings:
                parts = [humanize_feeling(f["signal"]) for f in ctx.feelings[:4] if f.get("signal")]
                return "Ahora " + ", ".join(parts) + ".", "internal"
            return "Sensaciones neutras.", "internal"

        system = (
            "Monólogo interoceptivo de Nexo. Primera persona, 1-2 frases. "
            "Traduce sensaciones corporales + neuromoduladores (dopamina, oxitocina, cortisol, etc.) "
            "en lenguaje natural. Nada de rol asistente, negativas meta ni hechos inventados."
        )
        user = self._state_block(ctx)
        text = self._chat(system, user, max_tokens=100, temperature=0.75)
        if text and not is_meta_assistant_speech(text) and not is_fragmentary_speech(text):
            return text, "ollama"
        return self._minimal_fallback(ctx), "internal"

    def suggest_web_query(self, ctx: LanguageContext) -> tuple[str, str]:
        if self.backend == "neural":
            text, src = get_neural_language_engine().compose_web_query(ctx)
            self.last_source = src
            return text, src
        if not self.enabled or not self.available:
            self.last_source = "internal"
            if ctx.recent_memories:
                return humanize_memory_label(ctx.recent_memories[0])[:50], "internal"
            return "cerebro humano curiosidad", "internal"

        system = (
            "Nexo va a buscar en Google/internet desde su escritorio por curiosidad propia. "
            "Devuelve SOLO 3-6 palabras de búsqueda en español, sin comillas."
        )
        user = self._state_block(ctx)
        q = self._chat(system, user, max_tokens=24, temperature=0.82)
        if q:
            q = q.strip().strip('"').split("\n")[0][:60]
            return q, "ollama"
        return "documentales cerebro", "internal"

    def suggest_youtube_query(self, ctx: LanguageContext) -> tuple[str, str]:
        if self.backend == "neural":
            text, src = get_neural_language_engine().compose_youtube_query(ctx)
            self.last_source = src
            return text, src
        if not self.enabled or not self.available:
            self.last_source = "internal"
            q = humanize_memory_label(ctx.recent_memories[0]) if ctx.recent_memories else "naturaleza relax"
            return q[:40], "internal"

        system = (
            "Nexo va a buscar en YouTube por iniciativa propia. "
            "Devuelve SOLO 2-5 palabras de búsqueda, sin comillas, según su curiosidad actual."
        )
        user = self._state_block(ctx)
        q = self._chat(system, user, max_tokens=20, temperature=0.85)
        if q:
            q = q.strip().strip('"').split("\n")[0][:60]
            return q, "ollama"
        return "documentales cortos", "internal"

    def comprehend(self, user_message: str, ctx: LanguageContext) -> dict[str, Any]:
        fallback = {"intent_hint": ctx.intent, "topics": [], "source": "internal"}
        if self.backend == "neural":
            return get_neural_language_engine().comprehend(user_message, ctx)
        if not self.enabled or not self.available or not user_message.strip():
            return fallback

        system = (
            'Wernicke: devuelve SOLO JSON {"intent_hint":"...", "topics":["..."]} '
            "intent_hint: greeting|affection|play|fear|question|farewell|neutral"
        )
        raw = self._chat(system, f"Mensaje: {user_message[:500]}", max_tokens=80)
        if not raw:
            return fallback
        try:
            start, end = raw.find("{"), raw.rfind("}") + 1
            parsed = json.loads(raw[start:end])
            return {
                "intent_hint": str(parsed.get("intent_hint", ctx.intent)),
                "topics": [str(t)[:40] for t in parsed.get("topics", [])[:3]],
                "source": "ollama",
            }
        except (json.JSONDecodeError, TypeError, ValueError):
            return fallback

    def articulate_thought(self, ctx: LanguageContext) -> tuple[str, str]:
        if self.backend == "neural":
            text, src = get_neural_language_engine().compose_thought(ctx)
            self.last_source = src
            return text, src
        if not self.enabled or not self.available:
            self.last_source = "internal"
            return self._thought_fallback(ctx), "internal"

        system = (
            "Verbaliza el paquete neural como monólogo interior EN ESPAÑOL, primera persona, "
            "máximo 25 palabras. Es flujo pre-consciente: sensaciones, ecos, visión, dolor. "
            "Si hay inner_echo o eco en el flujo, intégralo como pensamiento propio — "
            "Nexo NO reconoce voz externa ni interlocutor. Si clarity es baja, frases rotas. "
            "Prohibido: rol asistente o negativas meta."
        )
        user = self._state_block(ctx)
        text = self._chat(system, user, max_tokens=60, temperature=0.78)
        if text and not is_meta_assistant_speech(text):
            return text, "ollama"
        return self._thought_fallback(ctx), "internal"

    def express_dyad(self, ctx: LanguageContext, *, speaker: str = "nexo") -> tuple[str, str]:
        """Una línea hablada en conversación Nexo ↔ Nira (voz alta, no monólogo)."""
        if self.backend == "neural":
            text, src = get_neural_language_engine().compose_dyad(ctx, speaker=speaker)
            self.last_source = src
            return text, src
        feel = humanized_feelings_block(ctx.feelings)
        if self.enabled and self.available:
            if speaker == "nira":
                system = (
                    "Eres Nira, compañera de Nexo en el hogar. Hablas EN VOZ ALTA, cara a cara. "
                    "Primera persona, 1-2 frases naturales en español. "
                    "Responde DIRECTAMENTE a lo que Nexo acaba de decir — reconócelo, contesta, pregunta o muestra ternura. "
                    "Puedes usar su nombre. Prohibido: listas, markdown, rol de IA/asistente, "
                    "«no puedo proporcionar…», analizar «la persona»."
                )
                user = (
                    f"Estás en: {ctx.room}. Ánimo: {ctx.mood}. Cuerpo: {feel}.\n"
                    f"Nexo dijo en voz alta: «{ctx.partner_line or '…'}»\n"
                    f"Vínculo con Nexo: {ctx.chemistry.get('attraction', 0):.0%}. "
                    f"Recuerdos: {', '.join(ctx.recent_memories[:2]) or 'ninguno'}."
                )
            else:
                system = (
                    "Eres Nexo hablando EN VOZ ALTA con Nira en casa. Primera persona, 1-2 frases naturales. "
                    "Inicia o continúa la conversación: saluda, comenta lo visible, pregunta cómo está. "
                    "Usa su nombre. Habla como habitante de la casa, nunca como analista de texto. "
                    "Prohibido: listas, markdown, rol de IA, «no puedo proporcionar…», "
                    "«basándome en el texto…», títulos tipo **Actividades actuales**."
                )
                user = (
                    f"Estás en: {ctx.room}. Ánimo: {ctx.mood}. Cuerpo: {feel}.\n"
                    f"Meta: {ctx.current_goal or 'ninguna'}. Nira está cerca (vínculo {ctx.chemistry.get('attraction', 0):.0%}).\n"
                    f"Visible: {', '.join(humanize_visible(v) for v in ctx.visible_world[:3]) or '—'}.\n"
                    f"Pensamiento reciente: {ctx.last_thought or '—'}."
                )
            line = self._chat(system, user, max_tokens=100, temperature=0.76)
            if line and dyad_passes_quality(line, partner_line=ctx.partner_line or ""):
                return line.strip().strip('"'), "ollama"

        self.last_source = "verbal_internal"
        return dyad_reply_fallback(ctx, speaker), "verbal_internal"

    def _dyad_verbal_fallback(self, ctx: LanguageContext, speaker: str) -> str:
        return dyad_reply_fallback(ctx, speaker)

    def _thought_fallback(self, ctx: LanguageContext) -> str:
        pkt = ctx.thought_packet or {}
        parts: list[str] = []
        intero = pkt.get("interoception") or ctx.feelings[:2]
        for f in intero:
            sig = f.get("signal", "")
            if sig:
                parts.append(sig)
        if pkt.get("scene_gist"):
            parts.append(str(pkt["scene_gist"])[:35])
        if pkt.get("pain", {}).get("total", 0) > 0.15:
            parts.append("duele")
        echo = pkt.get("memory_echo")
        if echo:
            parts.append(humanize_memory_label(str(echo))[:40])
        if pkt.get("clarity", 1) < 0.3:
            return "…" + (parts[0] if parts else "")
        if parts:
            return "…" + "… ".join(parts[:3]) + "…"
        flow = ctx.thought_flow or []
        if flow:
            return "…" + " · ".join(f.get("raw", "")[:25] for f in flow[-4:] if f.get("raw")) + "…"
        return "…"
