"""
Interocepción: hambre, sed, temperatura, fatiga, confort.

Evoluciona con el tiempo y el entorno; alimenta la percepción y los impulsos motores.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BodyState:
    hunger: float = 0.28
    thirst: float = 0.22
    body_temp: float = 0.52
    fatigue: float = 0.2
    comfort: float = 0.62
    pleasure: float = 0.35
    satiety: float = 0.0
    bladder: float = 0.15
    hygiene: float = 0.18
    tick_count: int = 0
    pain_head: float = 0.0
    pain_torso: float = 0.0
    pain_limbs: float = 0.0
    pain_ache: float = 0.0
    baroreceptor_tone: float = 0.55
    cardiac_arousal: float = 0.0

    def tick(
        self,
        *,
        room_temp: float,
        activity: float,
        sleep_pressure: float,
        watching_tv: bool = False,
        strain: float = 1.0,
        ordeal_active: bool = False,
        circadian: dict | None = None,
    ) -> None:
        self.tick_count += 1
        circadian = circadian or {}
        circ_sleep = float(circadian.get("sleep_drive", 0.0) or 0.0)
        circ_alert = float(circadian.get("alertness", 0.5) or 0.5)
        rate = (0.004 + activity * 0.003) * max(0.5, strain)
        self.hunger = float(np.clip(self.hunger + rate, 0, 1))
        self.thirst = float(np.clip(self.thirst + rate * 1.15, 0, 1))
        self.bladder = float(np.clip(self.bladder + rate * 0.7, 0, 1))
        self.hygiene = float(np.clip(self.hygiene + rate * 0.45, 0, 1))
        circ_fatigue = 0.0022 * circ_sleep - 0.0012 * circ_alert
        self.fatigue = float(
            np.clip(
                self.fatigue
                + 0.002
                + sleep_pressure * 0.004
                + circ_fatigue
                - (0.01 if watching_tv else 0),
                0,
                1,
            )
        )
        drift = (room_temp - self.body_temp) * 0.06
        if "body_temp_target" in circadian:
            drift += (float(circadian["body_temp_target"]) - self.body_temp) * 0.025
        self.body_temp = float(np.clip(self.body_temp + drift, 0, 1))
        comfort = 1.0 - (
            0.32 * self.hunger
            + 0.22 * self.thirst
            + 0.18 * abs(self.body_temp - 0.52)
            + 0.12 * self.fatigue
            + 0.08 * self.bladder
            + 0.08 * self.hygiene
            + 0.14 * self.total_pain()
        )
        self.comfort = float(np.clip(comfort, 0, 1))

    def total_pain(self) -> float:
        return float(
            np.clip(
                0.35 * self.pain_head
                + 0.35 * self.pain_torso
                + 0.45 * self.pain_limbs
                + 0.25 * self.pain_ache,
                0,
                1,
            )
        )

    def pain_map(self) -> dict[str, float]:
        return {
            "head": round(self.pain_head, 3),
            "torso": round(self.pain_torso, 3),
            "limbs": round(self.pain_limbs, 3),
            "ache": round(self.pain_ache, 3),
            "total": round(self.total_pain(), 3),
        }

    def apply_pain(self, region: str, amount: float) -> None:
        amount = float(np.clip(amount, 0, 0.5))
        if region == "head":
            self.pain_head = float(np.clip(self.pain_head + amount, 0, 1))
        elif region == "limbs":
            self.pain_limbs = float(np.clip(self.pain_limbs + amount, 0, 1))
        elif region == "ache":
            self.pain_ache = float(np.clip(self.pain_ache + amount, 0, 1))
        else:
            self.pain_torso = float(np.clip(self.pain_torso + amount, 0, 1))

    def pain_stomach(self, amount: float) -> None:
        self.pain_torso = float(np.clip(self.pain_torso + amount, 0, 1))
        self.pain_ache = float(np.clip(self.pain_ache + amount * 0.5, 0, 1))

    def soothe_pain(self, amount: float = 0.15) -> None:
        f = 1.0 - float(np.clip(amount, 0, 0.5))
        self.pain_head *= f
        self.pain_torso *= f
        self.pain_limbs *= f
        self.pain_ache *= f

    def drink(self, amount: float = 0.35) -> None:
        self.thirst = float(np.clip(self.thirst - amount, 0, 1))

    def eat(self, amount: float = 0.4) -> None:
        self.hunger = float(np.clip(self.hunger - amount, 0, 1))

    def rest(self, amount: float = 0.25) -> None:
        self.fatigue = float(np.clip(self.fatigue - amount, 0, 1))

    def bathe(self, amount: float = 0.55) -> None:
        self.hygiene = float(np.clip(self.hygiene - amount, 0, 1))
        self.comfort = float(np.clip(self.comfort + amount * 0.25, 0, 1))
        self.body_temp = float(np.clip(self.body_temp + (0.52 - self.body_temp) * 0.15, 0, 1))

    def relieve(self, amount: float = 0.6) -> None:
        self.bladder = float(np.clip(self.bladder - amount, 0, 1))
        self.comfort = float(np.clip(self.comfort + amount * 0.12, 0, 1))

    def update_baroreceptors(self, heart_rate: float) -> None:
        """Interocepción cardíaca — pulso modula arousal suave."""
        target = float(np.clip(heart_rate / 120.0, 0.35, 1.25))
        self.baroreceptor_tone = float(np.clip(self.baroreceptor_tone * 0.88 + (1.0 - target) * 0.12, 0, 1))
        self.cardiac_arousal = float(np.clip(abs(target - 0.62) * 0.75, 0, 1))

    def encode(self, n: int) -> np.ndarray:
        vec = np.zeros(min(n, 12), dtype=np.float32)
        signals = [
            self.hunger,
            self.thirst,
            self.body_temp,
            self.fatigue,
            self.comfort,
            self.bladder,
            self.hygiene,
            max(0, self.body_temp - 0.55),
            max(0, 0.45 - self.body_temp),
            self.total_pain(),
            self.baroreceptor_tone,
            self.cardiac_arousal,
        ]
        for i, v in enumerate(signals):
            if i < vec.size:
                vec[i] = v
        return vec

    def feelings(self) -> list[dict]:
        """Sensaciones con intensidad para la UI (sin interpretar en texto fijo)."""
        items = [
            ("hambre", self.hunger),
            ("sed", self.thirst),
            ("temperatura", self.body_temp),
            ("fatiga", self.fatigue),
            ("confort", self.comfort),
            ("vejiga", self.bladder),
            ("higiene", self.hygiene),
        ]
        if self.pleasure > 0.12:
            items.append(("placer corporal", self.pleasure))
        if self.satiety > 0.2:
            items.append(("saciedad", self.satiety))
        cold = max(0.0, 0.48 - self.body_temp)
        heat = max(0.0, self.body_temp - 0.58)
        if cold > 0.12:
            items.append(("frío", cold))
        if heat > 0.12:
            items.append(("calor", heat))
        out = []
        for name, val in items:
            if val > 0.08:
                out.append({"signal": name, "intensity": round(float(val), 3)})
        if self.bladder > 0.55:
            out.append({"signal": "ganas de baño", "intensity": round(float(self.bladder), 3)})
        tp = self.total_pain()
        if tp > 0.12:
            region = max(
                [("cabeza", self.pain_head), ("pecho", self.pain_torso), ("extremidades", self.pain_limbs)],
                key=lambda x: x[1],
            )
            if region[1] > 0.1:
                out.append({"signal": f"dolor {region[0]}", "intensity": round(float(region[1]), 3)})
            if self.pain_ache > 0.15:
                out.append({"signal": "malestar general", "intensity": round(float(self.pain_ache), 3)})
        out.sort(key=lambda x: -x["intensity"])
        return out[:9]

    def drives(self) -> dict[str, float]:
        """Impulsos internos que sesgan acción (no diálogo)."""
        return {
            "seek_food": float(np.clip(self.hunger - 0.35, 0, 1)),
            "seek_water": float(np.clip(self.thirst - 0.4, 0, 1)),
            "seek_warmth": float(np.clip(0.45 - self.body_temp, 0, 1)),
            "seek_cool": float(np.clip(self.body_temp - 0.62, 0, 1)),
            "seek_rest": float(np.clip(self.fatigue - 0.45, 0, 1)),
            "seek_stimulus": float(np.clip(0.55 - self.comfort, 0, 1)),
            "seek_comfort": float(np.clip(0.42 - self.comfort, 0, 1)),
            "seek_bathroom": float(np.clip(self.bladder - 0.38, 0, 1)),
            "seek_hygiene": float(np.clip(self.hygiene - 0.35, 0, 1)),
            "seek_relief": float(np.clip(self.total_pain() - 0.2, 0, 1)),
        }

    def to_dict(self) -> dict:
        return {
            "hunger": round(self.hunger, 3),
            "thirst": round(self.thirst, 3),
            "body_temp": round(self.body_temp, 3),
            "fatigue": round(self.fatigue, 3),
            "comfort": round(self.comfort, 3),
            "pleasure": round(self.pleasure, 3),
            "satiety": round(self.satiety, 3),
            "bladder": round(self.bladder, 3),
            "hygiene": round(self.hygiene, 3),
            "pain": self.pain_map(),
            "feelings": self.feelings(),
            "drives": {k: round(v, 3) for k, v in self.drives().items()},
        }

    def load_dict(self, d: dict) -> None:
        for key in (
            "hunger", "thirst", "body_temp", "fatigue", "comfort",
            "pleasure", "satiety",
            "bladder", "hygiene", "pain_head", "pain_torso", "pain_limbs", "pain_ache",
        ):
            if key in d:
                setattr(self, key, float(d[key]))
        pain = d.get("pain")
        if isinstance(pain, dict):
            self.pain_head = float(pain.get("head", self.pain_head))
            self.pain_torso = float(pain.get("torso", self.pain_torso))
            self.pain_limbs = float(pain.get("limbs", self.pain_limbs))
            self.pain_ache = float(pain.get("ache", self.pain_ache))
