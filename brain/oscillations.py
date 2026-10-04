"""
Ritmos cerebrales ampliados — θ, γ, δ, β, spindles y acoplamiento cross-frequency.

No eligen acciones: modulan plasticidad, hipocampo, sueño y preparación motora.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class OscillatorSnapshot:
    theta_amp: float
    gamma_amp: float
    delta_amp: float
    beta_amp: float
    mode: str
    pac_coupling: float = 0.0
    spindle_active: float = 0.0
    motor_beta: float = 0.0


@dataclass
class BrainOscillators:
    theta_hz: float = 5.5
    gamma_hz: float = 42.0
    delta_hz: float = 1.2
    beta_hz: float = 18.0
    spindle_hz: float = 13.5
    dt_ms: float = 1.0
    theta_phase: float = 0.0
    gamma_phase: float = 0.0
    delta_phase: float = 0.0
    beta_phase: float = 0.0
    spindle_phase: float = 0.0
    _forced_mode: str | None = field(default=None, init=False)
    _forced_ticks: int = field(default=0, init=False)
    spindle_ticks_left: int = field(default=0, init=False)
    sleep_depth: float = field(default=0.0, init=False)
    last_snapshot: OscillatorSnapshot | None = field(default=None, init=False)

    def force_mode(self, mode: str, ticks: int) -> None:
        self._forced_mode = mode if mode in ("encode", "retrieve") else "retrieve"
        self._forced_ticks = max(1, int(ticks))

    def set_sleep_depth(self, depth: float) -> None:
        self.sleep_depth = float(np.clip(depth, 0.0, 1.0))

    def trigger_spindle_burst(self, *, ticks: int = 10) -> None:
        """Sleep spindle — NREM profundo (≈12–15 Hz)."""
        self.spindle_ticks_left = max(self.spindle_ticks_left, int(ticks))

    def _advance_phases(self) -> None:
        scale = self.dt_ms / 1000.0
        self.theta_phase = (self.theta_phase + 2 * np.pi * self.theta_hz * scale) % (2 * np.pi)
        self.gamma_phase = (self.gamma_phase + 2 * np.pi * self.gamma_hz * scale) % (2 * np.pi)
        self.delta_phase = (self.delta_phase + 2 * np.pi * self.delta_hz * scale) % (2 * np.pi)
        self.beta_phase = (self.beta_phase + 2 * np.pi * self.beta_hz * scale) % (2 * np.pi)
        self.spindle_phase = (self.spindle_phase + 2 * np.pi * self.spindle_hz * scale) % (2 * np.pi)

    @staticmethod
    def pac_modulate(theta_phase: float, gamma_amp: float) -> tuple[float, float]:
        """Acoplamiento fase-amplitud: γ más fuerte en fase θ favorable (codificación)."""
        coupling = 0.5 + 0.5 * np.cos(theta_phase - np.pi * 0.25)
        effective = float(gamma_amp * (0.72 + 0.28 * coupling))
        return effective, float(coupling)

    def step(
        self,
        *,
        sleep_state: str = "awake",
        motor_pending: bool = False,
    ) -> tuple[float, float, str]:
        snap = self.step_full(sleep_state=sleep_state, motor_pending=motor_pending)
        return snap.theta_amp, snap.gamma_amp, snap.mode

    def step_full(
        self,
        *,
        sleep_state: str = "awake",
        motor_pending: bool = False,
    ) -> OscillatorSnapshot:
        self._advance_phases()

        theta_amp = 0.6 + 0.4 * np.sin(self.theta_phase)
        gamma_amp = 0.55 + 0.45 * np.sin(self.gamma_phase)
        delta_amp = 0.35 + 0.65 * np.sin(self.delta_phase)
        beta_amp = 0.4 + 0.35 * np.sin(self.beta_phase)

        depth = self.sleep_depth
        if sleep_state in ("nrem_light", "nrem_deep", "sleep"):
            depth = max(depth, 0.45 if sleep_state == "nrem_light" else 0.75)
        if sleep_state == "rem":
            depth = min(depth, 0.25)
            theta_amp *= 1.08
            gamma_amp *= 0.92

        delta_amp = float(np.clip(delta_amp * (0.35 + 0.85 * depth), 0, 1.2))
        gamma_amp, pac = self.pac_modulate(self.theta_phase, gamma_amp)

        spindle = 0.0
        if self.spindle_ticks_left > 0:
            self.spindle_ticks_left -= 1
            spindle = float(0.55 + 0.45 * np.sin(self.spindle_phase))
            gamma_amp = float(np.clip(gamma_amp + spindle * 0.25, 0, 1.4))

        motor_beta = 0.0
        if motor_pending and sleep_state == "awake":
            motor_beta = float(0.45 + 0.4 * np.sin(self.beta_phase))
            beta_amp = float(np.clip(beta_amp + motor_beta, 0, 1.2))
            gamma_amp = float(np.clip(gamma_amp + motor_beta * 0.15, 0, 1.4))

        if self._forced_ticks > 0:
            self._forced_ticks -= 1
            mode = self._forced_mode or "retrieve"
            if self._forced_ticks == 0:
                self._forced_mode = None
        else:
            mode = "encode" if np.cos(self.theta_phase) > 0 else "retrieve"

        snap = OscillatorSnapshot(
            theta_amp=float(theta_amp),
            gamma_amp=float(gamma_amp),
            delta_amp=float(delta_amp),
            beta_amp=float(beta_amp),
            mode=mode,
            pac_coupling=float(pac),
            spindle_active=float(spindle),
            motor_beta=float(motor_beta),
        )
        self.last_snapshot = snap
        return snap

    @staticmethod
    def plasticity_gate(theta_amp: float, gamma_amp: float, *, delta_amp: float = 0.0) -> float:
        base = float(0.50 * theta_amp + 0.38 * gamma_amp + 0.12 * min(delta_amp, 1.0))
        return float(np.clip(base, 0.35, 1.25))

    def to_dict(self) -> dict[str, Any]:
        s = self.last_snapshot
        if not s:
            return {"theta_hz": self.theta_hz, "gamma_hz": self.gamma_hz}
        return {
            "theta_hz": self.theta_hz,
            "gamma_hz": self.gamma_hz,
            "delta_hz": self.delta_hz,
            "beta_hz": self.beta_hz,
            "mode": s.mode,
            "pac_coupling": round(s.pac_coupling, 3),
            "spindle": round(s.spindle_active, 3),
            "motor_beta": round(s.motor_beta, 3),
            "sleep_depth": round(self.sleep_depth, 3),
            "theta_amp": round(s.theta_amp, 3),
            "gamma_amp": round(s.gamma_amp, 3),
            "delta_amp": round(s.delta_amp, 3),
        }
