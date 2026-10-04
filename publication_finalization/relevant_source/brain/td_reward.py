"""
Dopamina predictiva (TD) — error de predicción de recompensa estilo VTA.

Libre albedrío (agency):
  - TD **nunca** elige ``choice_key`` ni fuerza el ganador de deliberación.
  - Solo (1) actualiza valores V(s,a), (2) pulsa DA vía nuclei, (3) aporta un
    sesgo Go **acotado** que el PFC puede anular (veto / no-go / agency).
  - Si hay conflicto prefrontal–límbico alto, el sesgo TD se atenúa aún más.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

# Sesgo máximo sobre el canal Go (deliberación sigue siendo soberana).
TD_GO_BIAS_MAX = 0.10
# Contribución máxima del |δ| al reward que alimenta DA.
TD_REWARD_GAIN = 0.45
DEFAULT_GAMMA = 0.92
DEFAULT_ALPHA = 0.18


def state_key(room: str, top_drive: str, hour_bucket: int = 0) -> str:
    return f"{room or '?'}|{top_drive or '?'}|{int(hour_bucket) % 8}"


@dataclass
class TDRewardSystem:
    """Tabla V(s,a) + último δ; no es un planificador."""

    gamma: float = DEFAULT_GAMMA
    alpha: float = DEFAULT_ALPHA
    values: dict[str, float] = field(default_factory=dict)
    last_delta: float = 0.0
    last_reward: float = 0.0
    last_state: str = ""
    last_action: str = ""
    last_go_biases: dict[str, float] = field(default_factory=dict)
    updates: int = 0

    def _v(self, s: str, a: str) -> float:
        return float(self.values.get(f"{s}::{a}", 0.0))

    def _set_v(self, s: str, a: str, v: float) -> None:
        self.values[f"{s}::{a}"] = float(np.clip(v, -1.5, 1.5))

    def predicted_value(self, room: str, top_drive: str, action: str, *, hour: int = 12) -> float:
        return self._v(state_key(room, top_drive, hour // 3), action)

    def go_biases(
        self,
        *,
        room: str,
        top_drive: str,
        hour: int,
        action_keys: list[str],
        conflict: float = 0.0,
    ) -> dict[str, float]:
        """
        Sesgo Go por acción ∈ [-TD_GO_BIAS_MAX, TD_GO_BIAS_MAX].
        Attenuado por conflicto PFC (protege voluntad ejecutiva).
        """
        s = state_key(room, top_drive, hour // 3)
        atten = float(np.clip(1.0 - 0.65 * conflict, 0.25, 1.0))
        out: dict[str, float] = {}
        for a in action_keys:
            raw = self._v(s, a)
            # Squash: valores altos no pueden dominar el net PFC.
            bias = float(np.tanh(raw) * TD_GO_BIAS_MAX * atten)
            if abs(bias) > 1e-4:
                out[a] = bias
        self.last_go_biases = dict(out)
        return out

    def observe(
        self,
        *,
        prev_room: str,
        prev_drive: str,
        action: str,
        reward: float,
        next_room: str,
        next_drive: str,
        hour: int = 12,
    ) -> float:
        """
        δ = r + γ max_a' V(s',a') - V(s,a)
        Actualiza V(s,a). No selecciona la siguiente acción.
        """
        if not action:
            self.last_delta = 0.0
            return 0.0
        s = state_key(prev_room, prev_drive, hour // 3)
        s2 = state_key(next_room, next_drive, hour // 3)
        v_sa = self._v(s, action)
        # Bootstrap: mejor valor estimado en s' (exploración de tabla, no política)
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

    @staticmethod
    def instantaneous_reward(
        *,
        valence: float,
        comfort_delta: float = 0.0,
        pleasure: float = 0.0,
        pain: float = 0.0,
        hunger: float = 0.0,
        surprise: float = 0.0,
    ) -> float:
        """Recompensa escalar para TD (homeostasis + afecto), no decisión."""
        r = (
            0.35 * float(valence)
            + 0.25 * float(np.clip(comfort_delta, -1, 1))
            + 0.20 * float(pleasure - 0.35)
            - 0.30 * float(pain)
            - 0.15 * float(max(0.0, hunger - 0.45))
            + 0.08 * float(surprise - 0.5)
        )
        return float(np.clip(r, -1.0, 1.0))

    def dopamine_pulse(self) -> float:
        """Señal [0,1] para nuclei/modulators a partir de δ (phasic DA)."""
        return float(np.clip(0.5 + TD_REWARD_GAIN * self.last_delta, 0.0, 1.0))

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled_path": "td_reward",
            "last_delta": round(self.last_delta, 4),
            "last_reward": round(self.last_reward, 4),
            "last_state": self.last_state,
            "last_action": self.last_action,
            "dopamine_pulse": round(self.dopamine_pulse(), 4),
            "go_biases": {k: round(v, 4) for k, v in list(self.last_go_biases.items())[:8]},
            "n_values": len(self.values),
            "updates": self.updates,
            "go_bias_max": TD_GO_BIAS_MAX,
            "agency_note": "TD biases Go only; PFC/deliberation selects actions",
        }
