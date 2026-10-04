"""
Hub multimodal con latencias por canal.

Canales: vision (0), audition (delay), proprioception (delay).
Ablation de un canal degrada tareas específicas (E7) sin forzar motor.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class SensoryChannel:
    name: str
    delay_ticks: int = 0
    noise: float = 0.02
    gain: float = 1.0
    enabled: bool = True
    _buf: deque = field(default_factory=deque, repr=False)

    def push(self, pattern: np.ndarray | None) -> np.ndarray | None:
        if pattern is None:
            self._buf.append(None)
        else:
            p = np.asarray(pattern, dtype=np.float32).ravel().copy()
            if self.noise > 0:
                p = np.clip(p + np.random.normal(0, self.noise, p.shape).astype(np.float32), 0, 1)
            self._buf.append(p * self.gain)
        while len(self._buf) > self.delay_ticks + 1:
            self._buf.popleft()
        if not self.enabled:
            return None
        if len(self._buf) <= self.delay_ticks:
            return None
        return self._buf[0]


@dataclass
class SensoryPathwayHub:
    vision_gain: float = 0.55
    audition_gain: float = 0.35
    somatic_gain: float = 0.4
    social_gain: float = 0.5
    last_modalities: list[str] = field(default_factory=list)
    # Multimodal delays (OFF hasta enable_multimodal_delays)
    use_delays: bool = False
    vision: SensoryChannel = field(
        default_factory=lambda: SensoryChannel("vision", delay_ticks=0, noise=0.01, gain=1.0)
    )
    audition: SensoryChannel = field(
        default_factory=lambda: SensoryChannel("audition", delay_ticks=2, noise=0.03, gain=0.9)
    )
    proprioception: SensoryChannel = field(
        default_factory=lambda: SensoryChannel("proprioception", delay_ticks=1, noise=0.02, gain=0.85)
    )
    last_fusion: dict[str, Any] = field(default_factory=dict)
    _ablate: set[str] = field(default_factory=set)

    def set_ablation(self, *channels: str) -> None:
        """Desactiva canales para E7 (vision / audition / proprioception)."""
        self._ablate = {c.lower() for c in channels}
        self.vision.enabled = "vision" not in self._ablate
        self.audition.enabled = "audition" not in self._ablate
        self.proprioception.enabled = "proprioception" not in self._ablate

    def clear_ablation(self) -> None:
        self.set_ablation()

    def route(self, brain: InfantApeBrain, vision: dict | None = None) -> dict[str, Any]:
        vision = vision or brain._last_vision or {}
        foveal = vision.get("foveal") or []
        modalities: list[str] = []
        salience_sum = 0.0

        for obj in foveal[:6]:
            mod = str(obj.get("modality", "world"))
            sal = float(obj.get("salience", 0.3))
            modalities.append(mod)
            salience_sum += sal
            if mod in ("visual", "world", "occipital"):
                self.vision_gain = float(np.clip(0.4 + sal * 0.5, 0.2, 1))
            elif mod in ("audio", "temporal", "social"):
                self.social_gain = float(np.clip(0.35 + sal * 0.45, 0.2, 1))
            elif mod in ("tactile", "parietal"):
                self.somatic_gain = float(np.clip(0.3 + sal * 0.5, 0.15, 1))

        if vision.get("caregiver", {}).get("visible"):
            self.social_gain = float(np.clip(self.social_gain + 0.25, 0, 1))
            modalities.append("social")

        self.last_modalities = modalities[:8]
        mean_sal = salience_sum / max(len(foveal), 1)

        # Ablation vision: reduce thalamic world/occipital
        v_scale = 1.0 if self.vision.enabled else 0.15
        a_scale = 1.0 if self.audition.enabled else 0.2
        p_scale = 1.0 if self.proprioception.enabled else 0.25

        brain.thalamus.gains["world"] = float(
            np.clip((1.0 + mean_sal * 0.15) * v_scale, 0.2, 1.35)
        )
        brain.thalamus.gains["social"] = float(
            np.clip((0.95 + self.social_gain * 0.3) * a_scale, 0.2, 1.45)
        )
        brain.thalamus.gains["occipital"] = float(
            np.clip((0.9 + self.vision_gain * 0.35) * v_scale, 0.2, 1.4)
        )
        brain.thalamus.gains["somatic"] = float(
            np.clip((0.9 + self.somatic_gain * 0.3) * p_scale, 0.2, 1.3)
        )

        return {
            "vision_gain": round(self.vision_gain * v_scale, 3),
            "social_gain": round(self.social_gain * a_scale, 3),
            "somatic_gain": round(self.somatic_gain * p_scale, 3),
            "modalities": self.last_modalities,
            "ablated": sorted(self._ablate),
            "delays": self.use_delays,
        }

    def fuse_patterns(
        self,
        *,
        vision_pat: np.ndarray | None,
        audio_pat: np.ndarray | None,
        proprio_pat: np.ndarray | None,
        n: int,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Fusiona canales con latencias. Si use_delays=False, mezcla inmediata.
        """
        if not self.use_delays:
            acc = np.zeros(n, dtype=np.float32)
            w = 0.0
            if vision_pat is not None and self.vision.enabled:
                v = np.asarray(vision_pat, dtype=np.float32).ravel()[:n]
                acc[: v.size] += v * self.vision_gain
                w += self.vision_gain
            if audio_pat is not None and self.audition.enabled:
                a = np.asarray(audio_pat, dtype=np.float32).ravel()[:n]
                acc[: a.size] += a * self.audition_gain
                w += self.audition_gain
            if proprio_pat is not None and self.proprioception.enabled:
                p = np.asarray(proprio_pat, dtype=np.float32).ravel()[:n]
                acc[: p.size] += p * self.somatic_gain
                w += self.somatic_gain
            if w > 1e-6:
                acc /= w
            self.last_fusion = {"mode": "immediate", "weight": round(w, 3)}
            return np.clip(acc, 0, 1), self.last_fusion

        self.vision.gain = self.vision_gain
        self.audition.gain = self.audition_gain
        self.proprioception.gain = self.somatic_gain
        delayed_v = self.vision.push(vision_pat)
        delayed_a = self.audition.push(audio_pat)
        delayed_p = self.proprioception.push(proprio_pat)

        acc = np.zeros(n, dtype=np.float32)
        present = []
        for name, pat, g in (
            ("vision", delayed_v, self.vision_gain),
            ("audition", delayed_a, self.audition_gain),
            ("proprioception", delayed_p, self.somatic_gain),
        ):
            if pat is None:
                continue
            present.append(name)
            p = pat.ravel()[:n]
            acc[: p.size] += p * g
        if present:
            acc /= max(len(present), 1)
        self.last_fusion = {
            "mode": "delayed",
            "present": present,
            "ablated": sorted(self._ablate),
        }
        return np.clip(acc, 0, 1), self.last_fusion

    def to_dict(self) -> dict[str, Any]:
        return {
            "vision_gain": round(self.vision_gain, 3),
            "audition_gain": round(self.audition_gain, 3),
            "somatic_gain": round(self.somatic_gain, 3),
            "social_gain": round(self.social_gain, 3),
            "modalities": list(self.last_modalities),
            "use_delays": self.use_delays,
            "ablated": sorted(self._ablate),
            "delays_ticks": {
                "vision": self.vision.delay_ticks,
                "audition": self.audition.delay_ticks,
                "proprioception": self.proprioception.delay_ticks,
            },
            "last_fusion": self.last_fusion,
        }
