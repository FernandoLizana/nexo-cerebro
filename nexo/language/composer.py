"""Compositor de enunciados — verbaliza estado interno sin LLM."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UtterancePlan:
    text: str
    intent: str
    source: str = "neural_template"
    engages_social: bool = False

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "text": self.text,
            "intent": self.intent,
            "source": self.source,
            "engages_social": self.engages_social,
        }


@dataclass
class UtteranceComposer:
    """Broca/Wernicke simplificado — plantillas desde estado cognitivo."""

    history: list[str] = field(default_factory=list)

    def compose(
        self,
        *,
        drives: dict[str, float],
        metacognitive_felt: str,
        metacognitive_doubt: float,
        workspace_labels: tuple[str, ...],
        last_action: str | None,
        caregiver_present: bool,
        trust: float,
        energy: float,
    ) -> UtterancePlan | None:
        if metacognitive_doubt > 0.55:
            plan = UtterancePlan("No lo tengo claro.", "uncertainty", engages_social=False)
        elif drives.get("hunger", 0.0) > 0.55 and energy < 0.4:
            plan = UtterancePlan("Tengo hambre.", "seek_food")
        elif drives.get("safety", 0.0) > 0.6:
            plan = UtterancePlan("Algo me preocupa.", "seek_safety")
        elif drives.get("social", 0.0) > 0.45 and caregiver_present:
            plan = UtterancePlan(
                "¿Estás ahí?" if trust > 0.5 else "…",
                "seek_contact",
                engages_social=True,
            )
        elif last_action == "approach_caregiver" and caregiver_present:
            plan = UtterancePlan("Me alegra verte.", "social_bond", engages_social=True)
        elif last_action == "rest" and drives.get("rest", 0.0) > 0.4:
            plan = UtterancePlan("Necesito descansar.", "seek_rest")
        elif metacognitive_felt == "claro" and workspace_labels:
            label = workspace_labels[0].split(":")[0]
            plan = UtterancePlan(f"Noto {label}.", "describe_state")
        elif last_action == "eat":
            plan = UtterancePlan("Eso ayudó.", "satisfaction")
        else:
            return None

        self.history.append(plan.text)
        if len(self.history) > 12:
            self.history.pop(0)
        return plan

    def caregiver_reply(self, *, agent_utterance: str, trust: float, social_need: float) -> str:
        lower = agent_utterance.lower()
        if "hambre" in lower:
            return "¿Quieres comer algo?"
        if "preocupa" in lower or "miedo" in lower:
            return "Estoy aquí, estás a salvo."
        if "descans" in lower:
            return "Descansa un poco."
        if "?" in agent_utterance or "ahí" in lower:
            return "Sí, te escucho." if trust > 0.4 else "…"
        if social_need > 0.5:
            return "Estoy contigo."
        return "De acuerdo."
