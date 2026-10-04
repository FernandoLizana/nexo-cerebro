"""
Subcortical: ganglios basales, tronco encefálico, cerebelo, área de Broca (lenguaje motor).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .deliberation import MOTOR_AFFINITY
from .caregiver_dialogue import caregiver_reply_fallback


@dataclass
class BasalGanglia:
    """Selección Go/No-Go de acciones motoras (exploración vs hábito)."""

    n_motor: int
    habit: np.ndarray = field(init=False)
    no_go: float = 0.25

    def __post_init__(self) -> None:
        self.habit = np.zeros(self.n_motor, dtype=np.float32)

    def gate(
        self,
        motor_v: np.ndarray,
        motor_spikes: np.ndarray,
        *,
        dopamine: float,
        drive: float,
        exploration: float,
        action_bias: np.ndarray | None = None,
        deliberation: dict[str, Any] | None = None,
        pfc_inhibition: float = 0.5,
        rng_seed: int | None = None,
    ) -> list[int]:
        scores = motor_v.astype(np.float32).copy()
        scores -= float(scores.mean())
        spike_mask = np.asarray(motor_spikes, dtype=bool)
        scores[spike_mask] += 2.5

        v_mean = float(scores.mean())
        v_std = float(scores.std())
        active_thresh = v_mean + max(0.08, v_std * 0.2)

        if deliberation:
            choice_key = str(deliberation.get("choice_key", ""))
            confidence = float(deliberation.get("confidence", 0.35))
            inhibited = bool(deliberation.get("inhibited", False))
            conflict = float(deliberation.get("conflict", 0.0))
            limbic_key = str(deliberation.get("limbic_winner_key", ""))

            if spike_mask.any():
                scores[spike_mask] += 0.25 + 0.55 * confidence

            for idx in MOTOR_AFFINITY.get(choice_key, []):
                if idx >= scores.size:
                    continue
                neural_active = bool(spike_mask[idx]) or float(motor_v[idx]) > active_thresh
                if neural_active:
                    scores[idx] += 0.55 + 0.85 * confidence
                else:
                    scores[idx] += 0.12 * confidence

            if inhibited and limbic_key and limbic_key != choice_key:
                inhibit = pfc_inhibition * (0.35 + conflict)
                for idx in MOTOR_AFFINITY.get(limbic_key, []):
                    if idx < scores.size:
                        scores[idx] -= inhibit

        scores += self.habit * (0.5 + dopamine)
        if action_bias is not None:
            bias = np.asarray(action_bias, dtype=np.float32).ravel()
            n = min(scores.size, bias.size)
            if n:
                scores[:n] += bias[:n] * (0.65 if deliberation else 1.0)
        seed = int(rng_seed if rng_seed is not None else 0) % (2**31)
        noise = np.random.default_rng(seed).normal(0, 0.4 * exploration, self.n_motor).astype(
            np.float32
        )
        scores += noise
        k = int(np.clip(round(2 + drive * 4 + exploration), 1, min(6, self.n_motor)))
        threshold = self.no_go
        if deliberation and deliberation.get("inhibited"):
            threshold += 0.06 + 0.04 * float(deliberation.get("conflict", 0))
        if float(scores.max()) < threshold:
            return []
        top = np.argpartition(scores, -k)[-k:]
        top = top[np.argsort(scores[top])[::-1]]
        self.habit[top] = np.clip(self.habit[top] + 0.04 * (0.5 + dopamine), 0, 3.0)
        return top.tolist()

    def reset(self) -> None:
        self.habit.fill(0.0)


@dataclass
class Brainstem:
    """Arousal global, presión de sueño (ciclo simplificado)."""

    arousal_bias: float = 0.42
    sleep_pressure: float = 0.0

    def modulate(self, time_ms: int, cortisol: float) -> float:
        self.sleep_pressure = float(np.clip(self.sleep_pressure + 0.00008 * time_ms, 0, 1))
        arousal = self.arousal_bias + 0.25 * cortisol - 0.35 * self.sleep_pressure
        return float(np.clip(arousal, 0.1, 1.0))

    def rest(self, amount: float = 0.3) -> None:
        self.sleep_pressure = float(np.clip(self.sleep_pressure - amount, 0, 1))


@dataclass
class Cerebellum:
    """Suavizado y coordinación temporal de patrones motores."""

    buffer: list[list[int]] = field(default_factory=list)

    def integrate(self, motor: list[int]) -> list[int]:
        if not motor:
            return motor
        self.buffer.append(list(motor))
        if len(self.buffer) > 8:
            self.buffer.pop(0)
        counts: dict[int, int] = {}
        for pat in self.buffer:
            for m in pat:
                counts[m] = counts.get(m, 0) + 1
        ranked = sorted(counts.items(), key=lambda x: -x[1])
        return [m for m, _ in ranked[: min(5, len(ranked))]]

    def reset(self) -> None:
        self.buffer.clear()


@dataclass
class BrocaArea:
    """Planificación de respuesta lingüística desde estado límbico (sin guiones)."""

    def plan(
        self,
        *,
        intent: str,
        mood: str,
        user: str,
        attachment: float,
        remembered: bool,
        memory_label: str | None,
        motor: list[int],
        arousal: float = 0.4,
        feelings: list[dict] | None = None,
        modulators: dict | None = None,
        chemistry: dict | None = None,
    ) -> str:
        if (user or "").strip():
            return caregiver_reply_fallback(
                user_message=user,
                intent=intent,
                mood=mood,
                room="",
                feelings=feelings,
                companion_present=chemistry is not None and chemistry.get("attraction", 0) > 0.45,
                memory_label=memory_label,
                remembered=remembered,
            )
        parts: list[str] = []
        if feelings:
            parts.append(feelings[0].get("signal", ""))
        if memory_label and remembered:
            parts.append(memory_label[:24])
        if chemistry and chemistry.get("attraction", 0) > 0.45:
            parts.append("cerca")
        oxy = (modulators or {}).get("oxytocin", 0)
        if oxy > 0.55:
            parts.append("calor")
        if not parts:
            parts.append(mood or "…")
        text = "…" + "… ".join(p for p in parts if p)[:80] + "…"
        if user and len(text) < 12:
            text = f"…{user[:30]}…"
        return text
