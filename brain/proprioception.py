"""
Propicepción articular fina — ángulos, carga tendinosa, postura esquelética.

Proyecta biomecánica a vector continuo para cerebelo y parietal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ProprioceptivePathway:
    joint_angles: dict[str, float] = field(default_factory=dict)
    tendon_load: dict[str, float] = field(default_factory=dict)
    posture: dict[str, float] = field(default_factory=dict)
    last_signal: float = 0.0

    def integrate(self, brain) -> tuple[np.ndarray, dict[str, Any]]:
        bm = brain.biomech
        sk = bm.skeleton_art if hasattr(bm, "skeleton_art") else None

        self.joint_angles = {
            k: float(np.clip(v, 0, 1))
            for k, v in bm.joint_stress.items()
        }
        self.tendon_load = dict(bm.tendon_load)
        self.posture = dict(bm.skeleton)

        if sk is not None and hasattr(sk, "joints"):
            for k, js in sk.joints.items():
                self.joint_angles[k] = float(np.clip(abs(js.angle) / 2.5, 0, 1))

        n = max(10, brain.n_sensory // 12)
        vec = np.zeros(n, dtype=np.float32)
        slots = list(self.joint_angles.values()) + list(self.posture.values())
        for i, v in enumerate(slots[: n - 2]):
            vec[i] = float(v)
        vec[-2] = float(np.clip(bm.equilibrium, 0, 1))
        vec[-1] = float(np.clip(max(bm.muscle_activation.values(), default=0), 0, 1))
        m = float(vec.max())
        if m > 1e-6:
            vec /= m
        self.last_signal = float(vec.mean())

        meta = {
            "joints": {k: round(v, 3) for k, v in list(self.joint_angles.items())[:8]},
            "posture": {k: round(v, 3) for k, v in self.posture.items()},
            "signal": round(self.last_signal, 3),
        }
        return vec, meta

    def to_dict(self) -> dict[str, Any]:
        return {
            "joint_angles": {k: round(v, 3) for k, v in list(self.joint_angles.items())[:10]},
            "posture": {k: round(v, 3) for k, v in self.posture.items()},
            "signal": round(self.last_signal, 3),
        }
