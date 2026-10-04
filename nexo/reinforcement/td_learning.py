"""Aprendizaje TD — error de predicción de recompensa (port simplificado)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

TD_GO_BIAS_MAX = 0.10
DEFAULT_GAMMA = 0.92
DEFAULT_ALPHA = 0.18


def state_key(top_drive: str, energy_bucket: int = 0) -> str:
    return f"room|{top_drive or '?'}|{int(energy_bucket) % 8}"


@dataclass
class TDRewardSystem:
    """Tabla V(s,a) + δ; no elige acciones directamente."""

    gamma: float = DEFAULT_GAMMA
    alpha: float = DEFAULT_ALPHA
    values: dict[str, float] = field(default_factory=dict)
    last_delta: float = 0.0
    last_reward: float = 0.0
    last_state: str = ""
    last_action: str = ""
    last_go_biases: dict[str, float] = field(default_factory=dict)
    updates: int = 0

    def _v(self, state: str, action: str) -> float:
        return float(self.values.get(f"{state}::{action}", 0.0))

    def _set_v(self, state: str, action: str, value: float) -> None:
        self.values[f"{state}::{action}"] = float(np.clip(value, -1.5, 1.5))

    def go_biases(
        self,
        *,
        top_drive: str,
        energy_bucket: int,
        action_keys: tuple[str, ...],
        conflict: float = 0.0,
    ) -> dict[str, float]:
        s = state_key(top_drive, energy_bucket)
        atten = float(np.clip(1.0 - 0.65 * conflict, 0.25, 1.0))
        out: dict[str, float] = {}
        for action in action_keys:
            raw = self._v(s, action)
            bias = float(np.tanh(raw) * TD_GO_BIAS_MAX * atten)
            if abs(bias) > 1e-4:
                out[action] = bias
        self.last_go_biases = dict(out)
        return out

    def observe(
        self,
        *,
        prev_drive: str,
        prev_energy_bucket: int,
        action: str,
        reward: float,
        next_drive: str,
        next_energy_bucket: int,
    ) -> float:
        if not action:
            self.last_delta = 0.0
            return 0.0
        s = state_key(prev_drive, prev_energy_bucket)
        s2 = state_key(next_drive, next_energy_bucket)
        v_sa = self._v(s, action)
        next_vals = [v for k, v in self.values.items() if k.startswith(s2 + "::")]
        v_next = max(next_vals) if next_vals else 0.0
        r = float(np.clip(reward, -1.0, 1.0))
        delta = r + self.gamma * v_next - v_sa
        self._set_v(s, action, v_sa + self.alpha * delta)
        self.last_delta = float(delta)
        self.last_reward = r
        self.last_state = s
        self.last_action = action
        self.updates += 1
        return self.last_delta
