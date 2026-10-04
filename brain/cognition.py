"""
Ciclo cognitivo diario de Nexo — integra percepción, atención, memoria,
decisión, emoción, predicción, hábitos, motivación y pensamiento interno.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .experiment_flags import get_flags
from .attention import AttentionBudget, competitive_filter


@dataclass
class ShortTermBuffer:
    """Memoria reciente (segundos–minutos simulados) con decaimiento."""

    items: list[dict] = field(default_factory=list)
    max_items: int = 12
    ttl_sec: float = 180.0

    def push(self, label: str, *, kind: str = "event", salience: float = 0.5, tags: list[str] | None = None) -> None:
        now = time.time()
        self.items = [i for i in self.items if now - i.get("ts", now) < self.ttl_sec]
        self.items.insert(
            0,
            {
                "label": label[:90],
                "kind": kind,
                "salience": round(float(salience), 3),
                "tags": list(tags or [])[:5],
                "ts": now,
            },
        )
        self.items = self.items[: self.max_items]

    def snapshot(self) -> list[dict]:
        now = time.time()
        return [
            {k: v for k, v in i.items() if k != "ts"}
            for i in self.items
            if now - i.get("ts", now) < self.ttl_sec
        ]


@dataclass
class HabitStore:
    """Conductas automatizadas (ahorro energético) — refuerzo desde ganglios basales."""

    routines: dict[str, float] = field(default_factory=dict)

    def cue_key(self, room: str, hour: int, drive: str) -> str:
        return f"{room}|{hour // 3}|{drive}"

    def suggest(self, room: str, hour: int, top_drive: str) -> dict | None:
        key = self.cue_key(room, hour, top_drive)
        strength = self.routines.get(key, 0.0)
        if strength < 0.22:
            return None
        action_map = {
            "seek_food": "ir a nevera",
            "seek_rest": "ir a cama",
            "seek_stimulus": "encender TV",
            "seek_hygiene": "bañarse",
            "seek_curiosity": "ir al escritorio",
            "seek_companion": "buscar a Nira",
        }
        return {"cue": key, "routine": action_map.get(top_drive, "deambular"), "strength": round(strength, 3)}

    def reinforce(self, room: str, hour: int, drive: str, dopamine: float) -> None:
        key = self.cue_key(room, hour, drive)
        self.routines[key] = float(np.clip(self.routines.get(key, 0) + 0.06 * (0.4 + dopamine), 0, 1))


@dataclass
class PredictiveModel:
    """Predicción: expectativas vs realidad → sorpresa → aprendizaje."""

    expectations: dict[str, str] = field(default_factory=dict)
    last_surprise: float = 0.0

    def predict(self, room: str, hour: int, drives: dict) -> str:
        top = max(drives.items(), key=lambda x: x[1]) if drives else ("", 0)
        drive, val = top
        if hour >= 22 or hour < 6:
            pred = "descanso en dormitorio"
        elif 7 <= hour < 10:
            pred = "desayuno en cocina"
        elif 17 <= hour < 22:
            pred = "tarde en sala o con Nira"
        elif drive == "seek_curiosity" and val > 0.35:
            pred = "explorar escritorio o cartas"
        else:
            pred = f"permanecer en {room}"
        self.expectations["next"] = pred
        return pred

    def observe(self, actual: str) -> float:
        expected = self.expectations.get("next", "")
        if not expected or not actual:
            self.last_surprise = 0.05
            return self.last_surprise
        exp_words = set(expected.lower().split())
        act_words = set(actual.lower().split())
        overlap = len(exp_words & act_words) / max(len(exp_words | act_words), 1)
        self.last_surprise = float(np.clip(1.0 - overlap, 0, 1))
        return self.last_surprise


@dataclass
class CognitiveCycle:
    """Orquesta los 14 procesos en un tick cognitivo."""

    stm: ShortTermBuffer = field(default_factory=ShortTermBuffer)
    habits: HabitStore = field(default_factory=HabitStore)
    prediction: PredictiveModel = field(default_factory=PredictiveModel)
    attention_focus: str = ""
    attention_salience: float = 0.0
    ignored_count: int = 0
    decision: str = ""
    decision_confidence: float = 0.0
    emotion_regulated: bool = False
    rumination: str = ""
    reward_expectation: float = 0.0
    last_summary: dict = field(default_factory=dict)
    attention_budget: AttentionBudget = field(default_factory=AttentionBudget)

    def run(
        self,
        brain,
        *,
        vision: dict | None,
        drives: dict,
        ambient: dict,
    ) -> dict[str, Any]:
        """Un ciclo: percibir → atender → recordar → predecir → decidir → regular."""
        room = brain.world.current_room()
        hour = int(ambient.get("hour", 12))
        body = brain.body
        flags0 = get_flags(brain)
        if hasattr(brain, "working_memory"):
            brain.working_memory.limited = bool(flags0.enable_limited_wm)

        # 1 Percepción unificada
        percepts = self._build_percepts(brain, vision, body, ambient)

        # 2 Atención — filtra por saliencia, peligro, interés
        attended, ignored = self._filter_attention(percepts, drives, brain)
        self.ignored_count = len(ignored)
        if attended:
            top = attended[0]
            self.attention_focus = top["label"]
            self.attention_salience = top["salience"]
            brain.world.point_attention(top.get("kind", "")) if top.get("kind") in (
                "tv", "bed", "fridge", "desk", "bath", "toilet", "sofa", "stove", "crop", "companion"
            ) else None

        # 3 Memoria — WM ya en brain.working_memory; STM buffer; LTM vía hippocampus
        for p in attended[:3]:
            self.stm.push(p["label"], kind=p.get("modality", "sense"), salience=p["salience"])
            brain.working_memory.push(
                label=p["label"],
                modality=p.get("modality", "world"),
                room=room,
                valence=p.get("valence", 0.0),
                goal=drives and max(drives, key=drives.get) if drives else None,
                salience=float(p.get("salience", 0.5)),
            )

        # 12 Predicción
        predicted = self.prediction.predict(room, hour, drives)
        surprise = self.prediction.observe(f"{room} — {self.attention_focus or 'idle'}")

        # Global Workspace — momento consciente antes de deliberación
        flags = get_flags(brain)
        if flags.enable_executive_cognition and hasattr(brain, "executive"):
            brain.executive.pre_deliberation(
                brain, drives=drives, surprise=surprise, attended=attended
            )
        if flags.enable_consciousness:
            conscious = brain.consciousness.integrate(
                brain,
                attended=attended,
                percepts=percepts,
                drives=drives,
                ambient=ambient,
                surprise=surprise,
            )
            if brain.consciousness.winners:
                top_kind = brain.consciousness.winners[0].kind
                if top_kind in (
                    "tv", "bed", "fridge", "desk", "bath", "toilet", "sofa", "stove", "crop", "companion"
                ):
                    brain.world.point_attention(top_kind)
        else:
            conscious = brain.consciousness.last or {}

        # 9 Recompensa / motivación (expectativa dopaminérgica)
        self.reward_expectation = float(
            np.clip(0.3 * brain.modulators.dopamine + 0.2 * (1 - surprise), 0, 1)
        )

        # 10 Hábitos
        top_drive = max(drives.items(), key=lambda x: x[1])[0] if drives else "seek_rest"
        habit = self.habits.suggest(room, hour, top_drive)

        # 4 Deliberación prefrontal (competencia Go/No-Go — no heurística max-drive)
        delib = brain.deliberation.run(
            brain,
            drives=drives,
            ambient=ambient,
            attended=attended,
            habit=habit,
            surprise=surprise,
        )
        if flags.enable_consciousness:
            brain.consciousness.sync_after_deliberation(brain)
            conscious = brain.consciousness.last
        self.decision = delib.choice
        self.decision_confidence = delib.confidence
        brain.working_memory.set_goal(self.decision)

        # 5 Regulación emocional (corteza frena impulsos)
        arousal = brain.amygdala.arousal
        if arousal > 0.65 and brain.brainstem.sleep_pressure < 0.5:
            damp = 0.08 * (1 + brain.modulators.serotonin)
            brain.amygdala.arousal = float(np.clip(arousal - damp, 0.1, 1))
            brain.amygdala.valence = float(np.clip(brain.amygdala.valence * 0.92, -1, 1))
            self.emotion_regulated = True
        else:
            self.emotion_regulated = False

        # 8 Pensamiento interno / rumiación
        self.rumination = self._inner_dialogue(brain, surprise, drives, predicted, delib)

        # Moduladores por sorpresa y dolor
        if surprise > 0.55:
            brain.modulators.norepinephrine = float(np.clip(brain.modulators.norepinephrine + 0.06, 0, 1))
            brain.modulators.acetylcholine = float(np.clip(brain.modulators.acetylcholine + 0.04, 0, 1))
        if body.total_pain() > 0.25:
            brain.modulators.cortisol = float(np.clip(brain.hypothalamus.cortisol + 0.03, 0, 1))
            brain.body.pain_ache = float(np.clip(body.pain_ache + 0.02 * brain.hypothalamus.cortisol, 0, 1))

        self.last_summary = {
            "perception": percepts[:6],
            "attention": {
                "focus": self.attention_focus,
                "salience": round(self.attention_salience, 3),
                "ignored": self.ignored_count,
                "budget": self.attention_budget.to_dict(),
            },
            "memory": {
                "working": brain.working_memory.snapshot()[:4],
                "working_load": brain.working_memory.to_dict(),
                "short_term": self.stm.snapshot()[:4],
                "long_term_count": brain.hippocampus.size,
            },
            "prediction": {"expected": predicted, "surprise": round(surprise, 3)},
            "decision": {
                "choice": self.decision,
                "confidence": round(self.decision_confidence, 3),
                "agency": round(delib.agency, 3),
                "conflict": round(delib.conflict, 3),
                "inhibited": delib.inhibited,
                "limbic_pull": delib.limbic_winner,
                "pfc_pull": delib.pfc_winner,
            },
            "deliberation": delib.to_dict(),
            "emotion": {
                "valence": round(brain.amygdala.valence, 3),
                "arousal": round(brain.amygdala.arousal, 3),
                "regulated": self.emotion_regulated,
            },
            "motivation": {"dopamine": round(brain.modulators.dopamine, 3), "reward_expectation": round(self.reward_expectation, 3)},
            "habit": habit,
            "inner_voice": self.rumination,
            "consciousness": conscious,
            "body": {
                "pain": body.pain_map(),
                "comfort": round(body.comfort, 3),
                "sleep_pressure": round(brain.brainstem.sleep_pressure, 3),
            },
        }
        return self.last_summary

    def _build_percepts(self, brain, vision, body, ambient) -> list[dict]:
        percepts: list[dict] = []
        if vision:
            for p in (vision.get("foveal") or [])[:4]:
                percepts.append({
                    "label": p.get("interpretation") or p.get("label", "vista"),
                    "modality": "vision",
                    "salience": float(p.get("salience", 0.5)),
                    "kind": p.get("kind", ""),
                    "valence": 0.0,
                })
            gist = vision.get("scene_gist")
            if gist:
                percepts.append({"label": gist[:80], "modality": "vision", "salience": 0.45, "kind": "scene"})
        for f in body.feelings()[:5]:
            percepts.append({
                "label": f["signal"],
                "modality": "interoception",
                "salience": float(f.get("intensity", 0.3)),
                "kind": "body",
                "valence": -0.2 if "dolor" in f["signal"] or "hambre" in f["signal"] else 0.1,
            })
        pain = body.pain_map()
        if pain.get("total", 0) > 0.15:
            percepts.append({
                "label": f"dolor corporal ({pain['total']:.0%})",
                "modality": "nociception",
                "salience": min(0.95, 0.5 + pain["total"]),
                "kind": "pain",
                "valence": -0.6,
            })
        if ambient.get("phase") == "night":
            percepts.append({"label": "oscuridad", "modality": "ambient", "salience": 0.35, "kind": "light"})
        if hasattr(brain, "temporal"):
            percepts.extend(brain.temporal.percepts(ambient.get("temporal")))
        comp = getattr(brain, "companion", None)
        if comp and np.hypot(comp.x - brain.world.agent_x, comp.y - brain.world.agent_y) < 80:
            percepts.append({
                "label": f"{comp.name} cerca",
                "modality": "social",
                "salience": 0.4 + brain.chemistry.attraction * 0.3,
                "kind": "companion",
                "valence": 0.3,
            })
        return sorted(percepts, key=lambda x: -x["salience"])

    def _filter_attention(self, percepts: list[dict], drives: dict, brain) -> tuple[list[dict], list[dict]]:
        if not percepts:
            return [], []
        flags = get_flags(brain)
        if flags.enable_attention_budget:
            goal = None
            if hasattr(brain, "working_memory"):
                goal = brain.working_memory.dominant_goal()
            if flags.enable_goal_stack and hasattr(brain, "agent_loop"):
                stack = getattr(brain.agent_loop, "goal_stack", None)
                top = stack.peek() if stack is not None else None
                if top is not None:
                    goal = top.label or goal
            attended, ignored, st = competitive_filter(
                percepts,
                drives=drives,
                acetylcholine=float(brain.modulators.acetylcholine),
                goal=goal,
                budget=4,
                state=self.attention_budget,
            )
            self.attention_budget = st
            return attended, ignored
        # Legacy (paper E1–E3): umbral simple
        threshold = 0.28 - 0.08 * brain.modulators.acetylcholine
        attended = [p for p in percepts if p["salience"] >= threshold]
        if not attended:
            attended = percepts[:2]
        ignored = [p for p in percepts if p not in attended]
        danger = [p for p in percepts if "dolor" in p["label"] or p.get("kind") == "pain"]
        if danger:
            attended = danger[:1] + [p for p in attended if p not in danger][:2]
        self.attention_budget = AttentionBudget(
            budget=4,
            used=len(attended[:4]),
            focus_source="legacy",
            focus_label=attended[0]["label"] if attended else "",
        )
        return attended[:4], ignored

    def _decide(
        self,
        brain,
        drives: dict,
        attended: list[dict],
        habit: dict | None,
        ambient: dict,
        surprise: float,
    ) -> tuple[str, float]:
        if not drives:
            return "deambular", 0.3
        ranked = sorted(drives.items(), key=lambda x: -x[1])
        best, score = ranked[0]
        if score < 0.2:
            return "deambular", 0.25
        labels = {
            "seek_food": "comer",
            "seek_water": "beber",
            "seek_rest": "descansar",
            "sleep_need": "dormir",
            "seek_warmth": "buscar calor",
            "seek_stimulus": "estimularse (TV)",
            "seek_curiosity": "explorar",
            "seek_companion": "acercarse a Nira",
            "seek_hygiene": "higiene",
            "seek_bathroom": "baño",
            "seek_relief": "aliviar dolor",
        }
        choice = labels.get(best, best.replace("seek_", ""))
        conf = float(np.clip(score + 0.1 * brain.modulators.dopamine - 0.15 * surprise, 0.15, 0.95))
        if habit and habit.get("strength", 0) > 0.4 and score < 0.45:
            choice = habit.get("routine", choice)
            conf = max(conf, habit["strength"])
        if attended and attended[0].get("kind") == "pain":
            choice = "atender dolor"
            conf = max(conf, 0.55)
        return choice, conf

    def _inner_dialogue(self, brain, surprise: float, drives: dict, predicted: str, delib) -> str:
        parts: list[str] = []
        if getattr(brain, "consciousness", None) and brain.consciousness.winners:
            w = brain.consciousness.winners[0]
            parts.append(f"[{w.label}]")
        if surprise > 0.5:
            parts.append("esto no era lo que esperaba")
        if brain.brainstem.sleep_pressure > 0.6:
            parts.append("cansancio")
        if drives.get("seek_curiosity", 0) > 0.35:
            parts.append("¿qué habrá allí?")
        if brain.body.total_pain() > 0.2:
            parts.append("duele")
        if delib.inhibited:
            parts.append(f"elijo {delib.choice} aunque el cuerpo pide otra cosa")
        elif delib.agency > 0.45:
            parts.append(f"decido {delib.choice}")
        if not parts:
            parts.append(f"…{predicted[:30]}…")
        return " · ".join(parts[:3])
    def to_dict(self) -> dict:
        return dict(self.last_summary) if self.last_summary else {}
