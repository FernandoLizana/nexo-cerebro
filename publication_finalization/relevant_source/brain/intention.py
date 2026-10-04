"""
Puente intención conductual → episodio neural → selección motora por spikes.

La deliberación PFC define la meta; se inyecta en sensorial/WM antes de simular;
los ganglios basales priorizan canales que dispararon bajo esa meta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .encode import encode_text
from .deliberation import MOTOR_AFFINITY, DeliberationResult

if TYPE_CHECKING:
    from .deliberation import PrefrontalDeliberation
    from .mind import InfantApeBrain


@dataclass
class IntentionCircuit:
    """Estado del último enlace decisión ↔ red."""

    choice_key: str = ""
    sensory_gain: float = 0.0
    pfc_gain: float = 0.0
    spike_channels: list[int] = field(default_factory=list)
    gated_channels: list[int] = field(default_factory=list)
    spike_aligned: bool = False
    pfc_veto: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice_key": self.choice_key,
            "sensory_gain": round(self.sensory_gain, 3),
            "pfc_gain": round(self.pfc_gain, 3),
            "spike_channels": self.spike_channels[:8],
            "gated_channels": self.gated_channels[:8],
            "spike_aligned": self.spike_aligned,
            "pfc_veto": self.pfc_veto,
        }


def merge_intention_into_sensory(
    sensory: np.ndarray,
    brain: InfantApeBrain,
    deliberation: PrefrontalDeliberation,
) -> tuple[np.ndarray, IntentionCircuit]:
    """Mezcla la acción ganadora en el vector que entra al tálamo/corteza."""
    delib = deliberation.last
    if not delib.choice_key:
        return sensory, IntentionCircuit()

    n_sens = brain.n_sensory
    n_pfc = brain.cortex.n_prefrontal
    deliberation._ensure_encodings(n_pfc)

    world_enc = encode_text(
        f"world_intent:{delib.choice_key}:{delib.choice}@{brain.world.current_room()}",
        n_sens,
    ).astype(np.float32)
    pfc_enc = deliberation._encodings.get(delib.choice_key)
    if pfc_enc is None:
        pfc_enc = encode_text(f"motor_schema:{delib.choice_key}", n_pfc).astype(np.float32)

    gain = float(np.clip(0.14 + 0.32 * delib.confidence + 0.1 * delib.agency, 0.12, 0.55))
    pfc_gain = float(np.clip(0.38 + 0.42 * delib.confidence, 0.25, 0.85))

    out = np.asarray(sensory, dtype=np.float32).copy()
    out = np.clip(out * (1.0 - gain * 0.4) + world_enc * gain, 0.0, 1.0)
    n = min(n_pfc, out.size, pfc_enc.size)
    if n > 0:
        out[:n] = np.clip(out[:n] * (1.0 - pfc_gain * 0.55) + pfc_enc[:n] * pfc_gain, 0.0, 1.0)

    meta = IntentionCircuit(
        choice_key=delib.choice_key,
        sensory_gain=gain,
        pfc_gain=pfc_gain,
    )
    return out, meta


def prime_prefrontal_wm(brain: InfantApeBrain, deliberation: PrefrontalDeliberation) -> None:
    """Refuerzo WM pre-episodio (persiste entre ticks dentro del episodio vía set_stimulus)."""
    delib = deliberation.last
    if not delib.choice_key:
        return
    n_pfc = brain.cortex.n_prefrontal
    deliberation._ensure_encodings(n_pfc)
    enc = deliberation._encodings.get(delib.choice_key)
    if enc is None:
        return
    gain = float(np.clip(0.45 + 0.4 * delib.confidence, 0.35, 0.9))
    # Sobrecarga de WM limita priming — no elige la acción.
    if hasattr(brain, "working_memory"):
        gain *= float(brain.working_memory.pfc_gain_scale())
    brain.cortex.prime_working_memory(enc, gain=gain)


def deliberation_gate_context(delib: DeliberationResult) -> dict[str, Any]:
    """Paquete ligero para ganglios basales (evita import circular)."""
    return {
        "choice_key": delib.choice_key,
        "confidence": delib.confidence,
        "agency": delib.agency,
        "conflict": delib.conflict,
        "inhibited": delib.inhibited,
        "limbic_winner_key": delib.limbic_winner_key,
        "pfc_winner_key": delib.pfc_winner_key,
    }


def record_spike_alignment(
    circuit: IntentionCircuit,
    *,
    motor_spikes: np.ndarray,
    motor: list[int],
) -> IntentionCircuit:
    circuit.spike_channels = np.flatnonzero(motor_spikes).tolist()[:12]
    circuit.gated_channels = list(motor)[:12]
    aff = set(MOTOR_AFFINITY.get(circuit.choice_key, []))
    circuit.spike_aligned = bool(aff & set(circuit.spike_channels)) or bool(
        aff & set(circuit.gated_channels)
    )
    return circuit


def enforce_pfc_motor_veto(
    motor: list[int],
    gate_ctx: dict[str, Any] | None,
    *,
    n_motor: int,
) -> tuple[list[int], bool]:
    """
    Si PFC inhibió el impulso límbico: bloquea motor impulsivo o vacío.
    Retorna (motor_filtrado, veto_aplicado).
    """
    if not gate_ctx or not gate_ctx.get("inhibited"):
        return motor, False

    choice_key = str(gate_ctx.get("choice_key", ""))
    limbic_key = str(gate_ctx.get("limbic_winner_key", ""))
    choice_aff = set(MOTOR_AFFINITY.get(choice_key, []))
    limbic_aff = set(MOTOR_AFFINITY.get(limbic_key, []))

    if not motor:
        return [], True

    motor_set = set(m for m in motor if 0 <= m < n_motor)
    if motor_set & limbic_aff and not (motor_set & choice_aff):
        return [], True

    filtered = [m for m in motor if m in choice_aff or m not in limbic_aff]
    if not filtered:
        return [], True
    return filtered, True


def sync_basal_habits(brain: InfantApeBrain, deliberation: PrefrontalDeliberation) -> None:
    """Unifica hábitos cognitivos ↔ canales motores de ganglios basales."""
    delib = deliberation.last
    if not delib.choice_key:
        return
    da = brain.modulators.dopamine
    bump = 0.05 * (0.45 + da)
    bg = brain.basal_ganglia
    for idx in MOTOR_AFFINITY.get(delib.choice_key, []):
        if idx < bg.habit.size:
            bg.habit[idx] = float(np.clip(bg.habit[idx] + bump, 0.0, 3.0))


def hippocampus_stress_factor(cortisol: float) -> float:
    """Estrés crónico reduce codificación hipocampal."""
    return float(np.clip(1.0 - 0.5 * max(0.0, cortisol - 0.3), 0.4, 1.0))
