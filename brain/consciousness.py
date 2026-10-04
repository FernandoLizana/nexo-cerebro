"""
Integrador de conciencia funcional — Global Workspace + Self-Model + metacognición.

No verbaliza ni decide motor: compite por acceso global y sesga deliberación PFC.
Teorías de referencia: Global Workspace (Baars/Dehaene), interocepción (ínsula),
monitoreo de conflicto (cíngulo), reportabilidad posterior vía lenguaje.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain

WORKSPACE_CAPACITY = 3

# Señales interoceptivas / visuales → esquemas motores posibles (sesgo, no orden)
SIGNAL_ACTION_HINTS: dict[str, tuple[str, ...]] = {
    "hambre": ("eat", "harvest", "cook"),
    "antojo": ("eat", "cook", "harvest"),
    "sed": ("drink", "eat"),
    "fatiga": ("rest", "sleep"),
    "cansancio profundo": ("rest", "sleep"),
    "dolor": ("relief", "rest"),
    "placer": ("wander", "rest"),
    "saciedad": ("wander", "rest"),
    "confort": ("rest", "wander"),
    "crop": ("harvest",),
    "stove": ("cook",),
    "fridge": ("eat", "cook"),
    "companion": ("companion",),
    "conflicto": ("wander", "relief"),
}

KIND_ACTION_HINTS: dict[str, tuple[str, ...]] = {
    "crop": ("harvest",),
    "stove": ("cook",),
    "fridge": ("eat",),
    "companion": ("companion",),
    "bed": ("rest", "sleep"),
    "sofa": ("rest",),
    "bath": ("hygiene",),
    "toilet": ("bathroom",),
    "desk": ("study", "research"),
    "tv": ("tv",),
}


@dataclass
class ConsciousCandidate:
    source: str
    label: str
    salience: float
    valence: float = 0.0
    modality: str = "internal"
    kind: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class SelfModel:
    """Yo persistente — continuidad corporal, espacial y narrativa."""

    identity: str = "Nexo"
    room: str = ""
    top_feeling: str = ""
    agency: float = 0.0
    last_choice: str = ""
    companion_near: bool = False
    temporal_felt: str = ""
    narrative: list[str] = field(default_factory=list)
    tick: int = 0

    def update(
        self,
        brain: InfantApeBrain,
        *,
        winner: ConsciousCandidate | None,
        ambient: dict,
        metacog: dict,
    ) -> None:
        self.tick += 1
        self.room = brain.world.current_room()
        self.companion_near = bool(getattr(brain, "_companion_near", lambda: False)())
        env = ambient or {}
        temporal = env.get("temporal") or {}
        if isinstance(temporal, dict):
            self.temporal_felt = str(temporal.get("felt") or env.get("clock") or "")[:60]
        if winner:
            self.top_feeling = winner.label[:48]
            self.narrative.insert(0, winner.label[:56])
            self.narrative = self.narrative[:8]

    def sync_deliberation(self, brain: InfantApeBrain) -> None:
        delib = brain.deliberation.last
        if not delib:
            return
        self.agency = round(float(delib.agency), 3)
        self.last_choice = delib.choice

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "room": self.room,
            "top_feeling": self.top_feeling,
            "agency": self.agency,
            "last_choice": self.last_choice,
            "companion_near": self.companion_near,
            "temporal_felt": self.temporal_felt,
            "narrative": self.narrative[:5],
            "tick": self.tick,
        }

    def load_dict(self, d: dict | None) -> None:
        if not d:
            return
        for k in ("identity", "room", "top_feeling", "last_choice", "temporal_felt"):
            if k in d:
                setattr(self, k, str(d[k]))
        if "agency" in d:
            self.agency = float(d["agency"])
        if "companion_near" in d:
            self.companion_near = bool(d["companion_near"])
        if "tick" in d:
            self.tick = int(d["tick"])
        if isinstance(d.get("narrative"), list):
            self.narrative = [str(x)[:56] for x in d["narrative"][:8]]


@dataclass
class ConsciousnessIntegrator:
    """Espacio de trabajo global — un momento consciente por tick cognitivo."""

    self_model: SelfModel = field(default_factory=SelfModel)
    winners: list[ConsciousCandidate] = field(default_factory=list)
    suppressed: list[str] = field(default_factory=list)
    metacognition: dict[str, Any] = field(default_factory=dict)
    action_bias: dict[str, float] = field(default_factory=dict)
    last: dict[str, Any] = field(default_factory=dict)
    _log: list[str] = field(default_factory=list)

    def integrate(
        self,
        brain: InfantApeBrain,
        *,
        attended: list[dict],
        percepts: list[dict],
        drives: dict,
        ambient: dict,
        surprise: float = 0.0,
    ) -> dict[str, Any]:
        insula = brain.insula.integrate(brain)
        cing = brain.cingulate.integrate(brain, surprise=surprise)
        states = brain.brain_states.integrate(brain, ambient)

        candidates = self._gather_candidates(
            brain,
            attended=attended,
            percepts=percepts,
            drives=drives,
            insula=insula,
            cing=cing,
            surprise=surprise,
        )
        self.winners = self._select_winners(candidates, capacity=WORKSPACE_CAPACITY)
        winner = self.winners[0] if self.winners else None

        self.suppressed = [
            c.label for c in sorted(candidates, key=lambda x: -x.salience)[WORKSPACE_CAPACITY : WORKSPACE_CAPACITY + 5]
        ]

        self.metacognition = self._metacognition(
            brain,
            winner=winner,
            candidates=candidates,
            cing=cing,
            states=states,
            surprise=surprise,
        )
        self.action_bias = self._action_bias(winner, self.winners, drives)

        self.self_model.update(
            brain,
            winner=winner,
            ambient=ambient,
            metacog=self.metacognition,
        )

        if winner and winner.salience > 0.38:
            brain.working_memory.push(
                label=winner.label,
                modality=winner.modality,
                room=brain.world.current_room(),
                valence=winner.valence,
                goal=brain.working_memory.dominant_goal(),
                tags=["conscious", winner.source],
            )

        self.last = self.to_dict()
        if winner and self.metacognition.get("clarity", 0) > 0.35:
            msg = f"consciente: {winner.label[:40]}"
            if self.metacognition.get("doubt", 0) > 0.45:
                msg += " (duda interna)"
            self._log.insert(0, msg)
            self._log = self._log[:6]

        return self.last

    def sync_after_deliberation(self, brain: InfantApeBrain) -> None:
        """Actualiza yo y agencia tras la decisión PFC del tick."""
        self.self_model.sync_deliberation(brain)
        self.metacognition["agency"] = self.self_model.agency
        self.last = self.to_dict()

    def replay_urgency(self) -> float:
        """Prioridad para replay según saliencia del foco consciente."""
        w = self.winners[0] if self.winners else None
        if not w:
            return 0.0
        doubt = float(self.metacognition.get("doubt", 0))
        return float(np.clip(w.salience + doubt * 0.25, 0, 1))

    def _gather_candidates(
        self,
        brain: InfantApeBrain,
        *,
        attended: list[dict],
        percepts: list[dict],
        drives: dict,
        insula: dict,
        cing: dict,
        surprise: float,
    ) -> list[ConsciousCandidate]:
        out: list[ConsciousCandidate] = []
        intero_boost = float(insula.get("interoceptive_salience", 0))

        for p in attended[:4]:
            sal = float(p.get("salience", 0.4))
            if p.get("modality") == "interoception":
                sal = float(np.clip(sal + intero_boost * 0.35, 0, 1))
            out.append(
                ConsciousCandidate(
                    source="attention",
                    label=str(p.get("label", ""))[:64],
                    salience=sal,
                    valence=float(p.get("valence", 0)),
                    modality=str(p.get("modality", "sense")),
                    kind=str(p.get("kind", "")),
                )
            )

        for f in brain.hedonics.feelings()[:4]:
            out.append(
                ConsciousCandidate(
                    source="hedonic",
                    label=f["signal"],
                    salience=float(f["intensity"]) * 0.85 + intero_boost * 0.15,
                    valence=0.25,
                    modality="interoception",
                    kind="hedonic",
                )
            )

        for p in percepts:
            if p.get("modality") != "interoception":
                continue
            sig = str(p.get("label", ""))
            if any(c.label == sig for c in out):
                continue
            out.append(
                ConsciousCandidate(
                    source="body",
                    label=sig,
                    salience=float(p.get("salience", 0.3)),
                    valence=float(p.get("valence", -0.1)),
                    modality="interoception",
                    kind="body",
                )
            )

        vision = brain._last_vision or {}
        fix = vision.get("fixation")
        if fix:
            out.append(
                ConsciousCandidate(
                    source="vision",
                    label=str(fix.get("interpretation") or fix.get("label", "vista"))[:64],
                    salience=float(fix.get("salience", 0.5)) * (0.9 + brain.brain_states.cortical_gain * 0.1),
                    valence=0.05,
                    modality="vision",
                    kind=str(fix.get("kind", "")),
                )
            )

        if surprise > 0.45:
            out.append(
                ConsciousCandidate(
                    source="prediction",
                    label="sorpresa — modelo desactualizado",
                    salience=float(np.clip(surprise * 0.75, 0.2, 0.85)),
                    valence=-0.15,
                    modality="internal",
                    kind="surprise",
                )
            )

        if float(cing.get("conflict_level", 0)) > 0.42:
            out.append(
                ConsciousCandidate(
                    source="conflict",
                    label="tensión interna — impulsos en conflicto",
                    salience=float(cing["conflict_level"]) * 0.7,
                    valence=-0.2,
                    modality="internal",
                    kind="conflict",
                )
            )

        wm = brain.working_memory.snapshot()[:2]
        for slot in wm:
            lab = slot.get("label", "")
            if lab and not any(c.label == lab for c in out):
                out.append(
                    ConsciousCandidate(
                        source="memory",
                        label=str(lab)[:64],
                        salience=0.32 + (0.12 if slot.get("remembered") else 0),
                        valence=float(slot.get("valence", 0)),
                        modality=str(slot.get("modality", "memory")),
                        kind="wm",
                    )
                )

        if brain.companion and getattr(brain, "_companion_near", lambda: False)():
            bond = float(brain.chemistry.seek_companion_drive())
            if bond > 0.15:
                out.append(
                    ConsciousCandidate(
                        source="social",
                        label=f"Nira cerca — vínculo",
                        salience=float(np.clip(0.35 + bond * 0.4, 0.2, 0.8)),
                        valence=0.3,
                        modality="social",
                        kind="companion",
                    )
                )

        for dk, dv in sorted(drives.items(), key=lambda x: -x[1])[:3]:
            if dv > 0.28:
                out.append(
                    ConsciousCandidate(
                        source="drive",
                        label=dk.replace("_", " "),
                        salience=float(dv) * 0.55,
                        valence=-0.05 if "pain" in dk or "sleep" in dk else 0.05,
                        modality="motivation",
                        kind=dk,
                    )
                )

        return out

    def _select_winners(
        self,
        candidates: list[ConsciousCandidate],
        *,
        capacity: int,
    ) -> list[ConsciousCandidate]:
        if not candidates:
            return [
                ConsciousCandidate(
                    source="idle",
                    label="quietud interior",
                    salience=0.22,
                    modality="internal",
                )
            ]
        merged: dict[str, ConsciousCandidate] = {}
        for c in candidates:
            key = c.label.lower().strip()
            if key in merged:
                prev = merged[key]
                prev.salience = float(np.clip(max(prev.salience, c.salience) + c.salience * 0.15, 0, 1))
            else:
                merged[key] = ConsciousCandidate(
                    source=c.source,
                    label=c.label,
                    salience=float(np.clip(c.salience, 0, 1)),
                    valence=c.valence,
                    modality=c.modality,
                    kind=c.kind,
                    meta=dict(c.meta),
                )
        ranked = sorted(merged.values(), key=lambda x: -x.salience)
        return ranked[: max(1, capacity)]

    def _metacognition(
        self,
        brain: InfantApeBrain,
        *,
        winner: ConsciousCandidate | None,
        candidates: list[ConsciousCandidate],
        cing: dict,
        states: dict,
        surprise: float,
    ) -> dict[str, Any]:
        total_sal = sum(c.salience for c in candidates) or 1.0
        w_sal = winner.salience if winner else 0.2
        clarity = float(
            np.clip(
                w_sal / total_sal * 1.4 * states.get("cortical_gain", 1.0),
                0.08,
                1.0,
            )
        )
        doubt = float(np.clip(cing.get("conflict_level", 0) + surprise * 0.25, 0, 1))
        delib = brain.deliberation.last
        agency = float(self.self_model.agency)

        if states.get("state") in ("drowsy", "deep_sleep", "nrem"):
            clarity *= 0.55
        if doubt > 0.5 and clarity > 0.3:
            felt = "dividido"
        elif clarity > 0.55:
            felt = "claro"
        elif clarity > 0.3:
            felt = "difuso"
        else:
            felt = "somnoliento" if states.get("state") != "awake" else "nublado"

        return {
            "clarity": round(clarity, 3),
            "doubt": round(doubt, 3),
            "agency": round(agency, 3),
            "felt": felt,
            "brain_state": states.get("state", "awake"),
            "confidence": round(float(np.clip(w_sal - doubt * 0.3, 0, 1)), 3),
        }

    def _action_bias(
        self,
        winner: ConsciousCandidate | None,
        winners: list[ConsciousCandidate],
        drives: dict,
    ) -> dict[str, float]:
        bias: dict[str, float] = {}
        for i, w in enumerate(winners):
            weight = w.salience * (1.0 if i == 0 else 0.45)
            hints: set[str] = set()
            lab = w.label.lower()
            for sig, actions in SIGNAL_ACTION_HINTS.items():
                if sig in lab:
                    hints.update(actions)
            if w.kind in KIND_ACTION_HINTS:
                hints.update(KIND_ACTION_HINTS[w.kind])
            if w.source == "drive" and w.kind:
                dk = w.kind
                if dk == "seek_food":
                    hints.update(("eat", "harvest", "cook"))
                elif dk == "seek_cook":
                    hints.update(("cook",))
                elif dk == "seek_rest" or dk == "sleep_need":
                    hints.update(("rest", "sleep"))
                elif dk == "seek_companion":
                    hints.update(("companion",))
                elif dk == "seek_curiosity":
                    hints.update(("study", "research", "wander"))
            for act in hints:
                bias[act] = float(np.clip(bias.get(act, 0) + weight * 0.42, 0, 0.55))
        return bias

    def apply_deliberation_bias(self, contestants: list[Any]) -> None:
        """Sesgo Go en competencia PFC — post-selección de candidatos motores."""
        if not self.action_bias:
            return
        for c in contestants:
            boost = self.action_bias.get(c.key, 0.0)
            if boost > 0:
                c.go = float(c.go + boost)

    def to_dict(self) -> dict[str, Any]:
        w = self.winners[0] if self.winners else None
        return {
            "workspace_capacity": WORKSPACE_CAPACITY,
            "winner": {
                "label": w.label if w else "",
                "source": w.source if w else "",
                "salience": round(w.salience, 3) if w else 0,
                "modality": w.modality if w else "",
                "kind": w.kind if w else "",
            },
            "winners": [
                {
                    "label": c.label,
                    "source": c.source,
                    "salience": round(c.salience, 3),
                    "modality": c.modality,
                    "kind": c.kind,
                }
                for c in self.winners
            ],
            "suppressed": self.suppressed[:5],
            "metacognition": dict(self.metacognition),
            "action_bias": {k: round(v, 3) for k, v in self.action_bias.items()},
            "self": self.self_model.to_dict(),
            "narrative": self.self_model.narrative[:5],
            "log": self._log[:4],
            "global_workspace": {
                "occupancy": len(self.winners),
                "capacity": WORKSPACE_CAPACITY,
                "top_salience": round(w.salience, 3) if w else 0.0,
            },
        }

    def load_dict(self, d: dict | None) -> None:
        if not d:
            return
        if isinstance(d.get("self"), dict):
            self.self_model.load_dict(d["self"])
        if isinstance(d.get("metacognition"), dict):
            self.metacognition = dict(d["metacognition"])
        if isinstance(d.get("action_bias"), dict):
            self.action_bias = {str(k): float(v) for k, v in d["action_bias"].items()}
        self.last = self.to_dict()
