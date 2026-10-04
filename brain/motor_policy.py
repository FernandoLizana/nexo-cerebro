"""
Política motora continua — velocidad/dirección como prior sobre schemas.

Libre albedrío:
  - Nunca escribe ``choice_key``.
  - Los schemas de deliberación son *priors* de heading; el PFC sigue eligiendo.
  - TD/DA solo modulan magnitud del vector (sesgo acotado).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain

# Mapeo índice motor cortical → (dx, dy) unitario
_DIR_VEC: dict[int, tuple[float, float]] = {
    0: (-1.0, 0.0),
    1: (1.0, 0.0),
    2: (0.0, -1.0),
    3: (0.0, 1.0),
}


@dataclass
class ContinuousMotorCommand:
    vx: float = 0.0
    vy: float = 0.0
    speed: float = 0.0
    interact: float = 0.0
    goal: tuple[float, float] | None = None
    prior_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vx": round(self.vx, 4),
            "vy": round(self.vy, 4),
            "speed": round(self.speed, 4),
            "interact": round(self.interact, 3),
            "goal": self.goal,
            "prior_key": self.prior_key,
            "agency_note": "Continuous motor is prior only; PFC selects choice_key",
        }


@dataclass
class ContinuousMotorPolicy:
    """Capa ligera sobre n_motor: vector 2D + interact suave."""

    alpha: float = 0.25  # mezcla spikes vs prior schema
    td_speed_gain: float = 0.12  # tope de sesgo por valor TD
    last: ContinuousMotorCommand = field(default_factory=ContinuousMotorCommand)
    _w_heading: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float32))
    updates: int = 0

    def decode(
        self,
        brain: InfantApeBrain,
        motor_indices: list[int],
        *,
        choice_key: str,
        choice_target: str = "",
        confidence: float = 0.4,
    ) -> ContinuousMotorCommand:
        """Combina spikes motores + prior de schema → comando continuo."""
        hx, hy = 0.0, 0.0
        interact = 0.0
        for m in motor_indices[:8]:
            mi = int(m)
            if mi == 4 or mi >= 5:
                interact = max(interact, 0.55)
            vec = _DIR_VEC.get(mi % 4 if mi not in (4,) else -1)
            if vec:
                hx += vec[0]
                hy += vec[1]

        # Prior desde schema (mueble objetivo) — no fuerza choice
        goal = None
        if choice_target and hasattr(brain, "world"):
            c = brain.world.furniture_center(choice_target)
            if c:
                goal = (float(c[0]), float(c[1]))
                dx = c[0] - brain.world.agent_x
                dy = c[1] - brain.world.agent_y
                norm = float(np.hypot(dx, dy)) + 1e-6
                px, py = dx / norm, dy / norm
                hx = (1.0 - self.alpha) * hx + self.alpha * px * (0.5 + 0.5 * confidence)
                hy = (1.0 - self.alpha) * hy + self.alpha * py * (0.5 + 0.5 * confidence)

        # Memoria de heading aprendida
        hx = 0.7 * hx + 0.3 * float(self._w_heading[0])
        hy = 0.7 * hy + 0.3 * float(self._w_heading[1])

        speed = float(np.clip(np.hypot(hx, hy), 0, 1.5))
        # TD: solo escala velocidad (acotado); no elige dirección ni choice_key
        if hasattr(brain, "td_reward") and getattr(brain, "experiment_flags", None):
            from .experiment_flags import get_flags

            if get_flags(brain).enable_td_reward:
                v = float(np.tanh(brain.td_reward.last_delta))
                speed = float(np.clip(speed * (1.0 + self.td_speed_gain * v), 0, 1.8))

        if speed > 1e-4:
            hx, hy = hx / (speed + 1e-6) * min(speed, 1.0), hy / (speed + 1e-6) * min(speed, 1.0)

        # Proyectar goal cercano a lo largo del vector
        if goal is None and speed > 0.2 and hasattr(brain, "world"):
            reach = 28.0 * min(speed, 1.0)
            goal = (
                float(brain.world.agent_x + hx * reach),
                float(brain.world.agent_y + hy * reach),
            )

        cmd = ContinuousMotorCommand(
            vx=float(hx),
            vy=float(hy),
            speed=float(min(speed, 1.5)),
            interact=float(interact),
            goal=goal,
            prior_key=choice_key,
        )
        self.last = cmd
        return cmd

    def learn(
        self,
        *,
        reward: float,
        dopamine: float = 0.5,
    ) -> None:
        """Actualiza heading con recompensa (no elige acción)."""
        cmd = self.last
        if cmd.speed < 0.05:
            return
        lr = 0.04 * (0.4 + 0.6 * dopamine)
        self._w_heading[0] = float(
            np.clip(self._w_heading[0] + lr * reward * cmd.vx, -1.2, 1.2)
        )
        self._w_heading[1] = float(
            np.clip(self._w_heading[1] + lr * reward * cmd.vy, -1.2, 1.2)
        )
        self.updates += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "last": self.last.to_dict(),
            "heading": [round(float(self._w_heading[0]), 3), round(float(self._w_heading[1]), 3)],
            "updates": self.updates,
        }

    def apply_to_world(self, brain: InfantApeBrain, cmd: ContinuousMotorCommand | None = None) -> list[int]:
        """
        Traduce comando continuo a walk_goal + códigos discretos compatibles.
        No toca deliberation.choice_key.
        """
        cmd = cmd or self.last
        discrete: list[int] = []
        if abs(cmd.vx) > 0.15:
            discrete.append(1 if cmd.vx > 0 else 0)
        if abs(cmd.vy) > 0.15:
            discrete.append(3 if cmd.vy > 0 else 2)
        if cmd.interact > 0.45:
            discrete.append(4)
        if cmd.goal is not None and cmd.speed > 0.12:
            brain.world.set_walk_goal(cmd.goal[0], cmd.goal[1])
        return discrete
