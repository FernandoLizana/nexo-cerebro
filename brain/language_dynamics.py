"""
Dinámica del lenguaje — Bloque H (items 77–84).

Prosodia, inner/outer speech, afasia, code-switch, currículos y tutor RAG.
Nunca escribe choice_key.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .experiment_flags import get_flags

_EN_MARKERS = re.compile(
    r"\b(hello|hi|hey|how|what|why|brain|thanks|please|you|the|good|morning)\b",
    re.I,
)
_ES_MARKERS = re.compile(
    r"\b(hola|qué|que|cómo|como|gracias|cerebro|por|favor|buenos|días|dias)\b",
    re.I,
)


@dataclass
class AphasiaLesion:
    broca: float = 0.0
    wernicke: float = 0.0


@dataclass
class LanguageDynamicsStack:
    last_channel: str = "outer"
    detected_lang: str = "es"
    aphasia: AphasiaLesion = field(default_factory=AphasiaLesion)
    last_prosody: dict[str, Any] = field(default_factory=dict)
    inner_last: str = ""
    outer_last: str = ""
    tutor_active: bool = False
    last_metrics: dict[str, Any] = field(default_factory=dict)

    def detect_language(self, text: str) -> str:
        t = text or ""
        en = len(_EN_MARKERS.findall(t))
        es = len(_ES_MARKERS.findall(t))
        if en > es + 1:
            self.detected_lang = "en"
        elif es >= en:
            self.detected_lang = "es"
        return self.detected_lang

    def apply_prosody(self, text: str, *, valence: float, arousal: float) -> tuple[str, dict[str, Any]]:
        """Marcadores prosódicos por valencia/arousal (item 80)."""
        if not text:
            return text, {}
        out = text.strip()
        meta: dict[str, Any] = {"valence": round(valence, 3), "arousal": round(arousal, 3)}
        if arousal > 0.72:
            if not out.endswith(("!", "…")):
                out = out.rstrip(".") + "!"
            meta["pace"] = "fast"
        elif arousal < 0.28:
            out = out.replace("!", ".").rstrip(".") + "…"
            meta["pace"] = "slow"
        else:
            meta["pace"] = "normal"
        if valence < -0.35:
            meta["tone"] = "flat"
            out = out.replace("!", ".").replace("?", ".")
        elif valence > 0.4:
            meta["tone"] = "warm"
        else:
            meta["tone"] = "neutral"
        self.last_prosody = meta
        return out, meta

    def apply_inner_speech(self, text: str) -> str:
        """Monólogo interior — fragmentario (item 81)."""
        t = (text or "").strip()
        if not t:
            return "…"
        if not t.startswith("…"):
            t = "…" + t
        if not t.endswith("…"):
            t = t.rstrip(".!? ") + "…"
        self.inner_last = t
        self.last_channel = "inner"
        return t

    def apply_outer_speech(self, text: str) -> str:
        """Voz al cuidador / diálogo — oraciones completas (item 81)."""
        t = (text or "").strip()
        t = t.lstrip("…").strip()
        if t and t[-1] not in ".!?":
            t += "."
        self.outer_last = t
        self.last_channel = "outer"
        return t

    def apply_broca_aphasia(self, text: str) -> str:
        sev = self.aphasia.broca
        if sev <= 0 or not text:
            return text
        words = text.split()
        keep = max(2, int(len(words) * (1.0 - 0.45 * sev)))
        tele = " ".join(words[:keep])
        tele = re.sub(r"[,;:]+\s*", " ", tele)
        if sev > 0.45:
            tele = tele.replace(" porque ", " ").replace(" cuando ", " ")
        return tele.rstrip(".") + "…"

    def distort_wernicke(self, packet) -> Any:
        """Comprensión alterada — afasia de Wernicke (item 82)."""
        sev = self.aphasia.wernicke
        if sev <= 0:
            return packet
        topics = list(packet.topics or [])
        if topics:
            topics = topics[1:] + topics[:1]
        else:
            topics = ["emoción"]
        intent_map = {
            "greeting": "question",
            "question": "neutral",
            "affection": "greeting",
            "neutral": "affection",
        }
        packet.topics = topics[:3]
        packet.intent = intent_map.get(packet.intent, packet.intent)
        packet.source = str(packet.source) + "+wernicke_lesion"
        return packet

    def code_switch_reply(self, text: str, *, user_message: str) -> str:
        """Mezcla ES/EN según idioma del cuidador (item 83)."""
        lang = self.detect_language(user_message)
        if lang != "en" or not text:
            return text
        low = text.lower()
        if "hola" in low and "hello" not in low:
            text = text.replace("Hola", "Hi", 1).replace("hola", "hi", 1)
        if "gracias" in low:
            text = text.replace("Gracias", "Thanks", 1)
        if "cómo estás" in low or "como estas" in low:
            text = "I'm okay… " + text
        return text

    def post_comprehend(self, brain, packet):
        flags = get_flags(brain)
        if not flags.enable_language_dynamics:
            return packet
        if flags.enable_wernicke_aphasia:
            self.aphasia.wernicke = 0.55
            packet = self.distort_wernicke(packet)
        else:
            self.aphasia.wernicke = 0.0
        if flags.enable_bilingual_codeswitch:
            self.detect_language(packet.raw_text)
        return packet

    def post_articulate(
        self,
        brain,
        text: str,
        ctx,
        *,
        channel: str = "outer",
    ) -> str:
        flags = get_flags(brain)
        if not flags.enable_language_dynamics:
            return text
        valence = float(getattr(ctx, "valence", 0))
        arousal = float(getattr(ctx, "arousal", 0.3))
        out = text
        if flags.enable_broca_aphasia:
            self.aphasia.broca = 0.5
            out = self.apply_broca_aphasia(out)
        else:
            self.aphasia.broca = 0.0
        if flags.enable_inner_outer_speech:
            if channel == "inner":
                out = self.apply_inner_speech(out)
            else:
                out = self.apply_outer_speech(out)
        if flags.enable_prosody:
            out, _ = self.apply_prosody(out, valence=valence, arousal=arousal)
        if flags.enable_bilingual_codeswitch:
            out = self.code_switch_reply(out, user_message=str(getattr(ctx, "user_message", "")))
        return out

    def ensure_tutor(self, brain) -> bool:
        """Activa tutor RAG neural sin LLM (item 84)."""
        if not get_flags(brain).enable_language_tutor_rag:
            self.tutor_active = False
            return False
        net = getattr(brain, "language_network", None)
        if net is not None:
            net.tutor.enabled = True
        self.tutor_active = True
        return True

    def bind_brain(self, brain) -> None:
        """Hook de inicio — tutor + flags de backend neural (item 77)."""
        flags = get_flags(brain)
        if not flags.enable_language_dynamics:
            return
        if flags.enable_neural_language_default:
            import os

            os.environ.setdefault("CEREBRO_LANGUAGE", "neural")
            os.environ.setdefault("CEREBRO_OLLAMA", "0")
        self.ensure_tutor(brain)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.last_channel,
            "detected_lang": self.detected_lang,
            "prosody": self.last_prosody,
            "inner_last": self.inner_last[:80],
            "outer_last": self.outer_last[:120],
            "aphasia": {"broca": round(self.aphasia.broca, 3), "wernicke": round(self.aphasia.wernicke, 3)},
            "tutor_active": self.tutor_active,
            "metrics": self.last_metrics,
            "agency_note": "Language articulates state only; PFC selects actions",
        }


def study_tracks_snapshot(brain) -> dict[str, Any]:
    """Los 7 tracks de estudio para verbalización (item 78)."""
    library_meta: dict[str, Any] = {"progress": 0.0, "total": 0, "last_title": "", "focus_ticks": 0}
    try:
        from .library import list_books

        books = list_books()
        n = len(books)
        library_meta = {
            "progress": float(np.clip(n / max(n, 8), 0, 1)) if n else 0.0,
            "total": n,
            "last_title": (books[0].get("name") or books[0].get("title") or "")[:48] if books else "",
            "focus_ticks": 0,
            "sections": [{"title": b.get("name", ""), "done": False} for b in books[:4]],
        }
    except Exception:
        pass
    return {
        "curriculum": brain.curriculum.to_dict(),
        "brain_facts": brain.brain_facts.to_dict(),
        "anatomy": brain.anatomy.to_dict(),
        "clinical": brain.clinical_neurology.to_dict(),
        "biopsych": brain.biopsych.to_dict(),
        "infant": brain.infant_brain.to_dict(),
        "library": library_meta,
    }
