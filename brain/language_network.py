"""
Red de lenguaje: Wernicke (comprensión) ↔ fascículo arqueado ↔ Broca (producción).

Fase 2: tutor en sombra + RAG de ejemplos aprendidos.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .caregiver_dialogue import (
    caregiver_reply_fallback,
    is_fragmentary_speech,
    reply_engages_caregiver,
)
from .character import classify_intent
from .encode import encode_text, stimulus_id
from .language_tutor_rag import (
    adapt_learned_exemplar,
    extract_exemplar,
    retrieve_learned_exemplars,
    tutor_memory_label,
)
from .dialogue_engine import (
    caregiver_passes_quality,
    dyad_passes_quality,
    dyad_reply_fallback,
    is_meta_assistant_speech,
)
from .verbalize import humanize_feeling
from .neural_language import get_neural_language_engine, resolve_language_backend
from .experiment_flags import get_flags

if TYPE_CHECKING:
    from .language_cortex import LanguageContext, LanguageCortex
    from .mind import InfantApeBrain


@dataclass
class ComprehensionPacket:
    """Salida Wernicke — qué entendió Nexo del cuidador."""

    raw_text: str
    intent: str
    topics: list[str]
    source: str = "internal"
    semantic_hits: list[dict] = field(default_factory=list)
    tutor_hits: list[dict] = field(default_factory=list)


@dataclass
class UtterancePlan:
    """Plan Broca — qué quiere decir antes de articular."""

    intent: str
    address_caregiver: bool
    echo_user: str
    state_clause: str
    room: str
    learned_exemplars: list[str] = field(default_factory=list)
    tutor_exemplar_new: str | None = None


@dataclass
class CaregiverExchangeResult:
    reply: str
    source: str
    comprehension: ComprehensionPacket
    plan: UtterancePlan
    tutor_learned: bool = False
    tutor_recalled: bool = False


@dataclass
class LanguageTutor:
    """
    Modelo externo solo para enseñar — no habla al cuidador directamente.
    Guarda ejemplos en memoria semántica vía learn_from_tutor().
    """

    enabled: bool = False
    model: str = ""
    max_exemplars_per_turn: int = 1
    learn_when_similarity_below: float = 0.72

    def fetch_exemplar(
        self,
        language: LanguageCortex,
        *,
        user_message: str,
        ctx: LanguageContext,
    ) -> str | None:
        if not self.enabled:
            return None
        if resolve_language_backend() != "ollama":
            return get_neural_language_engine().compose_tutor_exemplar(user_message, ctx)
        if not language.enabled:
            return None
        if not language.available and not language.ping():
            return None
        feel = humanize_feeling(ctx.feelings[0]["signal"]) if ctx.feelings else "estoy bien"
        system = (
            "Eres un tutor de lenguaje para Nexo (homínido). "
            "Genera UNA frase ejemplo en español que Nexo podría aprender. "
            "Primera persona. Reconoce al cuidador y responde directamente. "
            "Prohibido: listas de sensaciones sueltas, «…palabra…», decir que eres IA, "
            "negativas meta («no puedo proporcionar…»)."
        )
        user = (
            f"Cuidador dijo: «{user_message}»\n"
            f"Estado de Nexo: {feel}, ánimo {ctx.mood}, en {ctx.room or 'casa'}."
        )
        if ctx.learned_exemplars:
            user += "\nYa aprendió algo parecido: " + " | ".join(ctx.learned_exemplars[:1])
        line = language._chat(system, user, max_tokens=100, temperature=0.65)
        if (
            line
            and not is_fragmentary_speech(line)
            and not is_meta_assistant_speech(line)
            and reply_engages_caregiver(user_message, line)
            and len(line) > 12
        ):
            return line.strip()
        return None


@dataclass
class WernickeArea:
    """Comprensión: ventral — texto → significado + memoria."""

    def comprehend(
        self,
        brain: InfantApeBrain,
        message: str,
        ctx: LanguageContext,
        language: LanguageCortex,
    ) -> ComprehensionPacket:
        intent = classify_intent(message)
        parsed = language.comprehend(message, ctx)
        intent = parsed.get("intent_hint", intent)
        topics = list(parsed.get("topics") or [])
        hits = brain.memory_store.semantic_search(message, k=3, threshold=0.58)
        tutor_hits = retrieve_learned_exemplars(brain, message, k=2, threshold=0.48)
        return ComprehensionPacket(
            raw_text=message,
            intent=intent,
            topics=topics,
            source=str(parsed.get("source", "internal")),
            semantic_hits=[h for h in hits if h.get("label")],
            tutor_hits=tutor_hits,
        )


@dataclass
class BrocaArea:
    """Producción: dorsal — plan de respuesta desde comprensión + cuerpo."""

    def plan(
        self,
        packet: ComprehensionPacket,
        ctx: LanguageContext,
        *,
        learned_exemplars: list[str] | None = None,
        tutor_exemplar_new: str | None = None,
    ) -> UtterancePlan:
        feel = humanize_feeling(ctx.feelings[0]["signal"]) if ctx.feelings else "estoy bien"
        return UtterancePlan(
            intent=packet.intent,
            address_caregiver=True,
            echo_user=packet.raw_text[:80],
            state_clause=feel,
            room=ctx.room or "casa",
            learned_exemplars=list(learned_exemplars or []),
            tutor_exemplar_new=tutor_exemplar_new,
        )


@dataclass
class ArcuateBundle:
    """Fascículo arqueado — une comprensión con producción hablada."""

    def articulate(
        self,
        plan: UtterancePlan,
        ctx: LanguageContext,
        language: LanguageCortex,
    ) -> tuple[str, str]:
        for exemplar in plan.learned_exemplars:
            adapted = adapt_learned_exemplar(exemplar, plan.echo_user, ctx)
            if (
                adapted
                and not is_fragmentary_speech(adapted)
                and reply_engages_caregiver(plan.echo_user, adapted)
            ):
                return adapted, "learned"

        ctx.learned_exemplars = list(plan.learned_exemplars)
        if resolve_language_backend() == "neural":
            reply, src = get_neural_language_engine().compose_chat(ctx)
            if reply and caregiver_passes_quality(plan.echo_user, reply):
                return reply, src

        reply, src = language._express_chat(ctx)
        if (
            reply
            and src == "ollama"
            and not is_fragmentary_speech(reply)
            and caregiver_passes_quality(plan.echo_user, reply)
        ):
            return reply, src

        reply = caregiver_reply_fallback(
            user_message=plan.echo_user,
            intent=plan.intent,
            mood=ctx.mood,
            room=plan.room,
            feelings=ctx.feelings,
            visible=ctx.visible_world,
            companion_name=ctx.companion_name,
            companion_present=ctx.companion_present,
            voice_from_sky=ctx.caregiver_from_sky,
            memory_label=ctx.memory_label,
            remembered=ctx.remembered,
        )
        return reply, "caregiver_fallback"


@dataclass
class DyadExchangeResult:
    nexo_line: str
    nira_line: str
    nexo_source: str
    nira_source: str


@dataclass
class LanguageNetwork:
    wernicke: WernickeArea = field(default_factory=WernickeArea)
    broca: BrocaArea = field(default_factory=BrocaArea)
    arcuate: ArcuateBundle = field(default_factory=ArcuateBundle)
    tutor: LanguageTutor = field(default_factory=LanguageTutor)

    def learn_from_tutor(
        self,
        brain: InfantApeBrain,
        *,
        user_message: str,
        exemplar: str,
        intent: str,
    ) -> None:
        if not exemplar:
            return
        label = tutor_memory_label(user_message=user_message, exemplar=exemplar)
        blob = f"{user_message}\n{exemplar}".encode("utf-8")
        key = stimulus_id(blob, "language_tutor")
        pattern = encode_text(label, brain.n_sensory)
        brain.memory_store.store(
            key,
            pattern,
            label=label,
            modality="language_tutor",
            motor=[],
            valence=0.18,
            arousal=0.35,
            tags=["tutor", "language", intent, "caregiver"],
            room=brain.world.current_room(),
            body=brain.body.to_dict(),
        )
        brain.working_memory.push(
            label=label[:48],
            modality="language_tutor",
            room=brain.world.current_room(),
            remembered=True,
            valence=0.12,
            goal=brain.working_memory.dominant_goal() or "",
            tags=["tutor", "aprendizaje"],
        )

    def consolidate_tutor_on_sleep(self, brain: InfantApeBrain) -> dict[str, Any]:
        """Sueño: refuerza frases aprendidas del tutor en memoria de trabajo."""
        total = brain.memory_store.count_by_modality("language_tutor")
        hits = brain.memory_store.search_language_tutor("", k=8, threshold=0.0)
        recalled = 0
        for mem in hits:
            exemplar = extract_exemplar(mem)
            if not exemplar:
                continue
            brain.working_memory.push(
                label=exemplar[:52],
                modality="language_tutor",
                room=brain.world.current_room(),
                remembered=True,
                valence=0.1,
                goal="consolidar lenguaje",
                tags=["tutor", "sueño", "replay"],
            )
            recalled += 1
        return {"tutor_total": total, "tutor_recalled_sleep": recalled}

    def status(self, brain: InfantApeBrain) -> dict[str, Any]:
        return {
            "tutor_enabled": self.tutor.enabled,
            "tutor_model": self.tutor.model or None,
            "learned_phrases": brain.memory_store.count_by_modality("language_tutor"),
        }

    def caregiver_exchange(
        self,
        brain: InfantApeBrain,
        message: str,
        ctx: LanguageContext,
        language: LanguageCortex,
    ) -> CaregiverExchangeResult:
        packet = self.wernicke.comprehend(brain, message, ctx, language)
        if get_flags(brain).enable_language_dynamics and hasattr(brain, "language_dynamics"):
            packet = brain.language_dynamics.post_comprehend(brain, packet)
        learned_texts = [extract_exemplar(m) for m in packet.tutor_hits if extract_exemplar(m)]
        learned_texts = [t for t in learned_texts if t][:2]

        tutor_learned = False
        best_sim = float(packet.tutor_hits[0].get("similarity", 0)) if packet.tutor_hits else 0.0
        need_new_lesson = (
            self.tutor.enabled
            and (not learned_texts or best_sim < self.tutor.learn_when_similarity_below)
        )
        tutor_exemplar_new = None
        if need_new_lesson:
            ctx.learned_exemplars = learned_texts
            tutor_exemplar_new = self.tutor.fetch_exemplar(
                language, user_message=message, ctx=ctx
            )
            if tutor_exemplar_new:
                self.learn_from_tutor(
                    brain,
                    user_message=message,
                    exemplar=tutor_exemplar_new,
                    intent=packet.intent,
                )
                tutor_learned = True

        plan = self.broca.plan(
            packet,
            ctx,
            learned_exemplars=learned_texts,
            tutor_exemplar_new=tutor_exemplar_new,
        )
        ctx.learned_exemplars = learned_texts
        reply, src = self.arcuate.articulate(plan, ctx, language)
        if not caregiver_passes_quality(message, reply):
            reply = caregiver_reply_fallback(
                user_message=message,
                intent=packet.intent,
                mood=ctx.mood,
                room=ctx.room or "casa",
                feelings=ctx.feelings,
                visible=ctx.visible_world,
                companion_name=ctx.companion_name,
                companion_present=ctx.companion_present,
                voice_from_sky=ctx.caregiver_from_sky,
            )
            src = "caregiver_fallback"

        return CaregiverExchangeResult(
            reply=reply,
            source=src,
            comprehension=packet,
            plan=plan,
            tutor_learned=tutor_learned,
            tutor_recalled=bool(learned_texts) and src == "learned",
        )

    def dyad_exchange(
        self,
        brain: InfantApeBrain,
        ctx_nexo: LanguageContext,
        language: LanguageCortex,
    ) -> DyadExchangeResult:
        """Turno completo Nexo ↔ Nira con filtros de calidad."""
        nexo_line, nx_src = language.express_dyad(ctx_nexo, speaker="nexo")
        if not dyad_passes_quality(nexo_line):
            nexo_line = dyad_reply_fallback(ctx_nexo, "nexo")
            nx_src = "verbal_internal"

        nira_ctx = brain._language_context(
            ep=brain._last_ep or {},
            draft=brain._state_draft(brain._last_ep or {}),
            mode="world",
            companion_speaker=True,
            partner_line=nexo_line,
            thought_flow=ctx_nexo.thought_flow,
        )
        nira_line, nr_src = language.express_dyad(nira_ctx, speaker="nira")
        if not dyad_passes_quality(nira_line, partner_line=nexo_line):
            nira_line = dyad_reply_fallback(nira_ctx, "nira")
            nr_src = "verbal_internal"

        rel = getattr(brain, "relationship_model", None)
        if rel is not None:
            try:
                from .relationship_model import note_dyad_exchange

                note_dyad_exchange(
                    rel,
                    nexo_line=nexo_line,
                    nira_line=nira_line,
                    trigger="language_network",
                )
            except Exception:
                pass

        return DyadExchangeResult(
            nexo_line=nexo_line,
            nira_line=nira_line,
            nexo_source=nx_src,
            nira_source=nr_src,
        )


def tutor_from_env() -> LanguageTutor:
    raw = os.environ.get("CEREBRO_LANGUAGE_TUTOR")
    backend = resolve_language_backend()
    if raw is not None:
        enabled = raw.strip().lower() in ("1", "true", "yes", "on")
    elif backend == "ollama":
        enabled = os.environ.get("CEREBRO_OLLAMA", "0").strip().lower() not in (
            "0",
            "false",
            "no",
            "off",
        )
    else:
        enabled = True
    model = os.environ.get("CEREBRO_TUTOR_MODEL", "") or os.environ.get(
        "CEREBRO_OLLAMA_MODEL", "llama3.2:1b"
    )
    return LanguageTutor(enabled=enabled, model=model)
