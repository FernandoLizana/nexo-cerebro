"""
Pensamiento interno desde actividad cortical real — sin plantillas literarias.

Incluye flujo continuo (stream): micro-pensamientos encadenados como monólogo
pre-consciente; la corteza del lenguaje verbaliza el momento presente.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ThoughtGenerator:
    history: list[dict] = field(default_factory=list)
    stream: list[dict] = field(default_factory=list)
    max_history: int = 24
    max_stream: int = 48
    _last_link_id: int = field(default=0, init=False)

    def generate(
        self,
        brain,
        ep: dict | None = None,
        *,
        vision: dict | None = None,
    ) -> dict:
        ep = ep or getattr(brain, "_last_ep", None) or {}
        clarity = self._clarity(brain)
        assoc = self._associative_level(brain)
        sensory = self._sensory_level(brain)
        motor_act = self._motor_level(brain)

        prior = ep.get("prior") or {}
        hypo = ep.get("hypothalamus") or {}
        mods = brain.modulators.to_dict()

        wm_labels = [
            s.get("label", "")[:40]
            for s in brain.working_memory.snapshot()[:4]
            if s.get("label")
        ]
        dominant = getattr(brain, "_current_goal", lambda: None)()

        packet: dict[str, Any] = {
            "associative_mean": round(assoc, 3),
            "sensory_mean": round(sensory, 3),
            "motor_activity": round(motor_act, 3),
            "clarity": round(clarity, 3),
            "valence": round(float(ep.get("valence", brain.amygdala.valence)), 3),
            "arousal": round(float(ep.get("arousal", brain.amygdala.arousal)), 3),
            "mood": hypo.get("mood") or brain.persona.mood,
            "remembered": bool(ep.get("remembered")),
            "memory_echo": prior.get("label", "")[:50] or None,
            "memory_similarity": prior.get("similarity"),
            "dominant_drive": dominant,
            "working_memory": wm_labels,
            "room": brain.world.current_room(),
            "modulators": mods,
            "sleep_pressure": round(brain.brainstem.sleep_pressure, 3),
        }

        chem = getattr(brain, "chemistry", None)
        if chem:
            packet["bond"] = chem.to_dict()

        feelings = brain.body.feelings()[:4]
        if feelings:
            packet["interoception"] = [
                {"signal": f["signal"], "intensity": f["intensity"]} for f in feelings
            ]

        pain = brain.body.pain_map()
        if pain.get("total", 0) > 0.1:
            packet["pain"] = pain

        if vision:
            packet["visual_fixation"] = vision.get("fixation")
            packet["scene_gist"] = vision.get("scene_gist", "")[:120]

        curiosity = brain._merged_drives().get("seek_curiosity")
        if curiosity is not None:
            packet["seek_curiosity"] = round(curiosity, 3)

        env = getattr(brain, "_last_env", None) or {}
        temporal = env.get("temporal") or brain.temporal.last_observe
        if temporal:
            packet["temporal"] = {
                "felt": temporal.get("felt"),
                "clock": temporal.get("clock"),
                "phase": temporal.get("phase_label"),
                "passage": temporal.get("passage"),
            }

        conscious = getattr(brain, "consciousness", None)
        if conscious and conscious.last:
            cm = conscious.last
            packet["conscious_moment"] = cm.get("winner", {})
            packet["metacognition"] = cm.get("metacognition", {})
            if cm.get("self"):
                packet["self"] = cm["self"]

        draft = self._neural_draft(packet, clarity)
        stream_fragments = self._push_stream(brain, ep, vision=vision, clarity=clarity, packet=packet)

        thought = {
            "packet": packet,
            "draft": draft,
            "clarity": round(clarity, 3),
            "associative_activity": round(assoc, 3),
            "mood": packet["mood"],
            "text": draft,
            "stream": stream_fragments,
            "flow": self.stream_snapshot(10),
        }
        self.history.append(thought)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        return thought

    def _push_stream(
        self,
        brain,
        ep: dict,
        *,
        vision: dict | None,
        clarity: float,
        packet: dict,
    ) -> list[dict]:
        """Añade micro-pensamientos al flujo continuo."""
        new_frags: list[dict] = []
        prev = self.stream[-1] if self.stream else None
        link_id = self._last_link_id

        def add(kind: str, raw: str, intensity: float = 0.5) -> None:
            nonlocal link_id
            if not raw or intensity < 0.08:
                return
            link_id += 1
            frag = {
                "id": link_id,
                "kind": kind,
                "raw": raw[:80],
                "intensity": round(float(intensity), 3),
                "ts": round(time.time(), 3),
                "links_to": prev.get("id") if prev else None,
            }
            self.stream.append(frag)
            new_frags.append(frag)
            if len(self.stream) > self.max_stream:
                self.stream.pop(0)

        conscious = getattr(brain, "consciousness", None)
        if conscious and conscious.winners:
            w = conscious.winners[0]
            add("conscious", w.label, min(0.95, w.salience + 0.15))
            meta = conscious.metacognition or {}
            if meta.get("doubt", 0) > 0.45:
                add("meta", f"duda ({meta.get('felt', '?')})", meta.get("doubt", 0.4))

        if vision and vision.get("fixation"):
            fix = vision["fixation"]
            add("visual", fix.get("interpretation", fix.get("label", "")), fix.get("salience", 0.5))

        if vision and vision.get("scene_gist"):
            add("scene", vision["scene_gist"][:70], 0.45)

        for f in brain.body.feelings()[:2]:
            if "dolor" in f.get("signal", "") or f.get("signal") == "malestar general":
                add("pain", f["signal"], f["intensity"])
            elif f.get("intensity", 0) > 0.35:
                add("body", f["signal"], f["intensity"])

        pending = getattr(brain, "_pending_echo_glimmer", None)
        if pending:
            add("echo", pending[:50], 0.48)
            brain._pending_echo_glimmer = None

        if packet.get("temporal"):
            add("time", str(packet["temporal"].get("felt", "tiempo"))[:70], 0.48)

        if packet.get("memory_echo"):
            add("memory", str(packet["memory_echo"]), 0.55)

        if packet.get("dominant_drive"):
            add("drive", str(packet["dominant_drive"]), 0.4)

        if clarity < 0.32:
            add("drift", "…", 0.25)
        elif prev and prev.get("kind") == prev.get("kind") and new_frags:
            add("assoc", f"↳ {prev.get('raw', '')[:30]}", 0.3)

        self._last_link_id = link_id
        return new_frags

    def inject_fragment(self, kind: str, raw: str, intensity: float = 0.5) -> dict:
        """Inserta un micro-pensamiento en el flujo (eco, símbolo, etc.)."""
        prev = self.stream[-1] if self.stream else None
        self._last_link_id += 1
        frag = {
            "id": self._last_link_id,
            "kind": kind,
            "raw": raw[:80],
            "intensity": round(float(intensity), 3),
            "ts": round(time.time(), 3),
            "links_to": prev.get("id") if prev else None,
        }
        self.stream.append(frag)
        if len(self.stream) > self.max_stream:
            self.stream.pop(0)
        return frag

    def stream_snapshot(self, n: int = 12) -> list[dict]:
        return list(self.stream[-n:])

    def recent_echoes(self, n: int = 4) -> list[str]:
        return [f.get("raw", "") for f in self.stream if f.get("kind") == "echo"][-n:]

    def flow_text(self, n: int = 8) -> str:
        """Texto continuo del flujo para UI (sin Ollama)."""
        parts = []
        for frag in self.stream[-n:]:
            raw = frag.get("raw", "")
            if raw and raw != "…":
                parts.append(raw)
            elif raw == "…":
                parts.append("…")
        return " · ".join(parts) if parts else "…"

    def _neural_draft(self, packet: dict, clarity: float) -> str:
        slim = {k: v for k, v in packet.items() if v is not None and v != [] and v != {}}
        if clarity < 0.28:
            slim["fragmentation"] = "high"
        return json.dumps(slim, ensure_ascii=False)

    def _clarity(self, brain) -> float:
        dop = brain.modulators.dopamine
        sleep = brain.brainstem.sleep_pressure
        ach = brain.modulators.acetylcholine
        gaba = brain.modulators.gaba_tone
        pain_penalty = brain.body.total_pain() * 0.25
        base = 0.2 + 0.38 * dop + 0.22 * ach - 0.42 * sleep - 0.12 * gaba - pain_penalty
        return float(np.clip(base, 0.05, 0.92))

    def _associative_level(self, brain) -> float:
        pop = brain.cortex.associative
        denom = max(pop.v_thresh - pop.v_rest, 1.0)
        act = np.clip((pop.v - pop.v_rest) / denom, 0, 1.25)
        sp = float(act[pop.spikes].mean()) if pop.spikes.any() else 0.0
        return float(0.65 * act.mean() + 0.35 * sp)

    def _sensory_level(self, brain) -> float:
        pop = brain.cortex.sensory
        denom = max(pop.v_thresh - pop.v_rest, 1.0)
        act = np.clip((pop.v - pop.v_rest) / denom, 0, 1.25)
        return float(act.mean())

    def _motor_level(self, brain) -> float:
        ep = getattr(brain, "_last_ep", None) or {}
        motor = ep.get("motor") or []
        if not motor:
            return 0.0
        return float(min(1.0, len(motor) / max(brain.cortex.n_motor, 1) * 2.5))

    def recent(self, n: int = 5) -> list[dict]:
        return list(self.history[-n:])
