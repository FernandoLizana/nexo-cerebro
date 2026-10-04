"""
Esqueleto articulado — huesos, articulaciones, torque, ragdoll y onda de choque espinal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

G = 9.81
DT = 0.33

SPINE_NAMES: tuple[str, ...] = ("sacral", "lumbar", "thoracic", "cervical")

LIMB_JOINTS: tuple[str, ...] = (
    "hip_l", "knee_l", "ankle_l",
    "hip_r", "knee_r", "ankle_r",
    "shoulder_l", "elbow_l",
    "shoulder_r", "elbow_r",
)


@dataclass
class JointState:
    angle: float = 0.0
    angular_velocity: float = 0.0
    torque: float = 0.0
    stress: float = 0.0
    angle_min: float = -2.8
    angle_max: float = 2.8


@dataclass
class ArticulatedSkeleton:
    """Cadena ósea humanoide con propagación de choque en columna."""

    joints: dict[str, JointState] = field(default_factory=dict)
    spine_shock: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    spine_angles: dict[str, float] = field(default_factory=lambda: {
        "sacral": 0.0, "lumbar": 0.0, "thoracic": 0.0, "cervical": 0.0,
    })
    pelvis_pitch: float = 0.0
    pelvis_roll: float = 0.0
    ragdoll_mode: bool = False

    def __post_init__(self) -> None:
        if not self.joints:
            limits = {
                "hip_l": (-0.4, 1.6), "hip_r": (-0.4, 1.6),
                "knee_l": (-0.1, 2.4), "knee_r": (-0.1, 2.4),
                "ankle_l": (-0.8, 0.9), "ankle_r": (-0.8, 0.9),
                "shoulder_l": (-1.2, 2.0), "shoulder_r": (-1.2, 2.0),
                "elbow_l": (-0.2, 2.6), "elbow_r": (-0.2, 2.6),
            }
            for name in LIMB_JOINTS:
                lo, hi = limits.get(name, (-2.5, 2.5))
                self.joints[name] = JointState(angle_min=lo, angle_max=hi)

    def inject_spinal_shock(self, impulse: float, *, entry: int = 0) -> None:
        """Impulso en columna → onda ascendente (sacral → cervical)."""
        idx = int(np.clip(entry, 0, len(self.spine_shock) - 1))
        self.spine_shock[idx] = float(np.clip(self.spine_shock[idx] + impulse, 0, 1.2))

    def propagate_spine(self) -> float:
        """Propaga la onda de choque segmento a segmento con decaimiento."""
        w = list(self.spine_shock)
        new = [0.0] * len(w)
        for i in range(len(w)):
            new[i] = w[i] * 0.78
            if i > 0:
                new[i] += w[i - 1] * 0.52
            if i < len(w) - 1:
                new[i] += w[i + 1] * 0.18
        self.spine_shock = [float(np.clip(v, 0, 1)) for v in new]
        for i, name in enumerate(SPINE_NAMES):
            self.spine_angles[name] = float(np.clip(self.spine_angles[name] * 0.85 + self.spine_shock[i] * 0.35, -0.9, 0.9))
        return max(self.spine_shock)

    def drive_gait(self, gait: str, phase: float, muscle: float) -> None:
        """Torques musculares hacia postura de marcha (no ragdoll)."""
        if self.ragdoll_mode:
            return
        swing = float(np.sin(phase * np.pi * 2))
        amp = 0.45 * muscle if gait == "walk" else (0.65 * muscle if gait == "run" else 0.12)
        targets = {
            "hip_l": swing * amp,
            "hip_r": -swing * amp,
            "knee_l": max(0, -swing) * amp * 1.1,
            "knee_r": max(0, swing) * amp * 1.1,
            "ankle_l": swing * 0.25 * amp,
            "ankle_r": -swing * 0.25 * amp,
            "shoulder_l": -swing * amp * 0.7,
            "shoulder_r": swing * amp * 0.7,
            "elbow_l": 0.35 + abs(swing) * 0.2,
            "elbow_r": 0.35 + abs(swing) * 0.2,
        }
        for name, target in targets.items():
            j = self.joints.get(name)
            if not j:
                continue
            err = target - j.angle
            j.torque = float(np.clip(err * 8.0 - j.angular_velocity * 2.2, -12, 12))

    def ragdoll_step(self, *, body_angle: float, in_water: bool) -> None:
        """Gravedad + inercia angular en cada articulación (ragdoll)."""
        self.ragdoll_mode = True
        grav = G * 0.015 * (0.35 if in_water else 1.0)
        for name, j in self.joints.items():
            lever = 0.4 if "hip" in name or "shoulder" in name else 0.25
            j.torque = grav * lever * (1 if "l" in name[-1:] else -1) * np.sin(j.angle + body_angle)
            j.torque -= j.angular_velocity * (2.5 if in_water else 1.2)
            j.angular_velocity += j.torque * DT * 0.08
            j.angle += j.angular_velocity * DT
            j.angle = float(np.clip(j.angle, j.angle_min, j.angle_max))
            j.stress = float(np.clip(abs(j.torque) * 0.08 + abs(j.angular_velocity) * 0.12, 0, 1))

        self.pelvis_pitch += body_angle * 0.4
        self.pelvis_roll += sum(j.angular_velocity for j in self.joints.values()) * 0.002
        self.propagate_spine()

    def integrate_joints(self, gait: str, phase: float, muscle: float) -> None:
        """Integra torques → ángulos articulares."""
        if self.ragdoll_mode:
            return
        self.drive_gait(gait, phase, muscle)
        for j in self.joints.values():
            j.angular_velocity += j.torque * DT * 0.06
            j.angular_velocity *= 0.88
            j.angle += j.angular_velocity * DT
            j.angle = float(np.clip(j.angle, j.angle_min, j.angle_max))
            j.stress = float(np.clip(abs(j.torque) * 0.06 + abs(j.angular_velocity) * 0.1, 0, 1))

    def settle_ragdoll(self) -> None:
        """Recuperación post-ragdoll hacia neutral."""
        self.ragdoll_mode = False
        for j in self.joints.values():
            j.angle *= 0.82
            j.angular_velocity *= 0.5
            j.torque = 0.0
        for k in self.spine_angles:
            self.spine_angles[k] *= 0.75
        self.spine_shock = [v * 0.5 for v in self.spine_shock]
        self.pelvis_pitch *= 0.7
        self.pelvis_roll *= 0.7

    def joint_stress_map(self) -> dict[str, float]:
        out = {name: round(j.stress, 3) for name, j in self.joints.items()}
        spine_total = max(self.spine_shock) if self.spine_shock else 0.0
        out["spine"] = round(float(np.clip(spine_total + sum(self.spine_angles.values()) * 0.05, 0, 1)), 3)
        return out

    def export_bones(self) -> dict[str, Any]:
        """Ángulos para el renderer 3D."""
        bones: dict[str, Any] = {
            "pelvis": {"pitch": round(self.pelvis_pitch, 3), "roll": round(self.pelvis_roll, 3)},
            "spine": {k: round(v, 3) for k, v in self.spine_angles.items()},
            "spine_shock": [round(v, 3) for v in self.spine_shock],
        }
        for name, j in self.joints.items():
            bones[name] = {"flex": round(j.angle, 3), "torque": round(j.torque, 2)}
        return bones

    def load_bones(self, data: dict | None) -> None:
        if not data:
            return
        pelvis = data.get("pelvis") or {}
        self.pelvis_pitch = float(pelvis.get("pitch", self.pelvis_pitch))
        self.pelvis_roll = float(pelvis.get("roll", self.pelvis_roll))
        spine = data.get("spine") or {}
        if isinstance(spine, dict):
            for k, v in spine.items():
                if k in self.spine_angles:
                    self.spine_angles[k] = float(v)
        shock = data.get("spine_shock")
        if isinstance(shock, list) and len(shock) == len(self.spine_shock):
            self.spine_shock = [float(x) for x in shock]
        for name in LIMB_JOINTS:
            block = data.get(name)
            if isinstance(block, dict) and name in self.joints:
                self.joints[name].angle = float(block.get("flex", self.joints[name].angle))
