"""
Personaje Nexo: vínculo social, diálogo e impulsos del hipotálamo.
Perfil bebé/simio: respuestas más emotivas, menos filtro verbal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


def classify_intent(text: str) -> str:
    t = text.lower().strip()
    if re.search(r"\b(hola|buenas|hey|saludos|qué tal)\b", t):
        return "greeting"
    if re.search(r"\b(adiós|chao|hasta luego|nos vemos)\b", t):
        return "farewell"
    if re.search(r"\b(te quiero|quiero|amor|abrazo|cariño|gracias|beso)\b", t):
        return "affection"
    if re.search(r"\b(jugar|juego|baila|corre|divertid)\b", t):
        return "play"
    if re.search(r"\b(miedo|asusta|malo|odio|no me gusta)\b", t):
        return "fear"
    if "?" in t or re.search(r"\b(qué|cómo|por qué|quién|cuándo|dónde)\b", t):
        return "question"
    return "neutral"


@dataclass
class Persona:
    name: str = "Nexo"
    species_label: str = "homínido en desarrollo"
    mood: str = "calm"
    message: str = "Hola… aún estoy formando mi cerebro. ¿Me hablas?"
    energy: float = 0.7
    familiarity: float = 0.0
    attachment: float = 0.35
    last_modality: str = ""
    last_label: str = ""
    experiences: int = 0
    learned: list[dict] = field(default_factory=list)
    dialogue: list[dict] = field(default_factory=list)

    MOOD_EMOJI = {
        "calm": "😌",
        "curious": "🤔",
        "content": "😊",
        "excited": "🤩",
        "stressed": "😰",
        "uneasy": "😕",
        "sleepy": "😴",
    }

    def add_turn(self, role: str, content: str) -> None:
        self.dialogue.append({"role": role, "text": content})
        if len(self.dialogue) > 40:
            self.dialogue.pop(0)

    def react(
        self,
        *,
        hypothalamus: dict,
        valence: float,
        arousal: float,
        modality: str,
        label: str,
        remembered: bool,
        motor: list[int],
        memory_hit: dict | None,
        reply: str | None = None,
    ) -> dict:
        self.mood = hypothalamus.get("mood", self.mood)
        self.energy = hypothalamus.get("energy", self.energy)
        self.familiarity = hypothalamus.get("familiarity", self.familiarity)
        self.attachment = float(
            min(1.0, self.attachment + 0.03 * hypothalamus.get("oxytocin", 0.3))
        )
        self.last_modality = modality
        self.last_label = label
        self.experiences += 1

        if reply:
            self.message = reply
        elif remembered and memory_hit:
            self.message = f"…{memory_hit.get('label', label)[:30]}…"
        else:
            self.message = "…"

        self.learned.append(
            {"label": label[:40], "modality": modality, "mood": self.mood, "valence": round(valence, 3)}
        )
        if len(self.learned) > 24:
            self.learned.pop(0)
        return self.to_dict()

    def converse(
        self,
        user_text: str,
        *,
        broca_reply: str,
        hypothalamus: dict,
    ) -> dict:
        self.add_turn("user", user_text)
        self.add_turn("nexo", broca_reply)
        self.message = broca_reply
        self.mood = hypothalamus.get("mood", self.mood)
        self.energy = hypothalamus.get("energy", self.energy)
        self.familiarity = hypothalamus.get("familiarity", self.familiarity)
        self.attachment = float(
            min(1.0, self.attachment + 0.04 * hypothalamus.get("oxytocin", 0.35))
        )
        return self.to_dict()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species_label": self.species_label,
            "mood": self.mood,
            "emoji": self.MOOD_EMOJI.get(self.mood, "🧠"),
            "message": self.message,
            "energy": round(self.energy, 3),
            "familiarity": round(self.familiarity, 3),
            "attachment": round(self.attachment, 3),
            "last_modality": self.last_modality,
            "last_label": self.last_label,
            "experiences": self.experiences,
            "learned": list(self.learned[-8:]),
            "dialogue": list(self.dialogue[-12:]),
        }
