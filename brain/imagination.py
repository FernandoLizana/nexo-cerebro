"""
Imaginación — flujo continuo del «ojo de la mente» (Drubach et al., Rev Neurol 2007).

Información generada intrínsecamente: recombinación de fragmentos de memoria declarativa,
manipulación en memoria de trabajo, eco perceptual y componente motor — sin estímulo externo.
"""

from __future__ import annotations

import base64
import hashlib
import io
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .encode import encode_image

if TYPE_CHECKING:
    from .mind import InfantApeBrain

IMG_SIZE = 256
NEURAL_ENCODE_INTERVAL = 5
STREAM_HISTORY = 12


def _mood_palette(mood: str, valence: float, arousal: float) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    presets = {
        "excited": ((255, 120, 60), (180, 40, 120)),
        "content": ((255, 200, 120), (100, 160, 200)),
        "stressed": ((80, 30, 90), (200, 50, 40)),
        "uneasy": ((60, 50, 100), (140, 80, 60)),
        "curious": ((120, 180, 255), (255, 220, 100)),
        "calm": ((40, 80, 120), (180, 210, 230)),
        "sleepy": ((20, 30, 60), (80, 90, 140)),
    }
    if mood in presets:
        return presets[mood]
    t = (valence + 1) / 2
    c1 = (int(80 + t * 175), int(60 + (1 - t) * 80), int(120 + arousal * 100))
    c2 = (int(40 + arousal * 140), int(80 + t * 100), int(160 - t * 80))
    return c1, c2


def _seed_from_parts(*parts: str) -> int:
    raw = "|".join(str(p) for p in parts if p)
    return int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)


@dataclass
class ImaginationEngine:
    """Generador continuo de imágenes mentales procedurales."""

    last: dict | None = field(default=None, init=False)
    _frame: int = field(default=0, init=False)
    _history: list[dict] = field(default_factory=list, init=False)
    _last_neural_frame: int = field(default=0, init=False)

    def advance_stream(
        self,
        brain: InfantApeBrain,
        *,
        thought: dict,
        vision: dict | None = None,
    ) -> dict:
        """Siempre emite un fotograma del flujo interior (streaming)."""
        self._frame += 1
        packet = thought.get("packet") or {}
        clarity = float(thought.get("clarity") or packet.get("clarity") or 0.28)
        assoc = float(thought.get("associative_activity") or packet.get("associative_mean") or 0.2)
        motor_act = float(packet.get("motor_activity") or 0)

        sources, fragments = self._brain_sources(brain, packet, vision)
        involuntary = self._involuntary_fragment(brain, packet)
        if involuntary:
            sources.append("espontáneo")
            fragments.insert(0, involuntary)

        scene = self._compose_scene(
            packet,
            vision,
            fragments=fragments,
            sources=sources,
            frame=self._frame,
            motor_act=motor_act,
            clarity=max(0.22, clarity),
            assoc=assoc,
        )
        png_bytes = self._render(scene)
        if not png_bytes:
            return self.last or {"active": False, "streaming": False}

        modality = "visual"
        if motor_act > 0.45:
            modality = "motor-visual"
            sources.append("imaginería motora")
        if packet.get("interoception"):
            sources.append("interocepción")

        caption = scene.get("caption", "flujo interior…")
        if self._should_encode_neurally(scene, clarity, assoc):
            pattern = encode_image(png_bytes, brain.n_sensory)
            brain._run_episode(
                pattern,
                modality="image",
                label=f"imaginación: {caption[:48]}",
                repeats=1,
                steps_per_repeat=18,
                tags=["imagination", "internal", "stream", scene.get("mood", "neutral")],
            )
            self._last_neural_frame = self._frame
            if self._frame % (NEURAL_ENCODE_INTERVAL * 3) == 0:
                brain._log_autonomy(f"imaginó — {caption[:40]}")

        result = {
            "active": True,
            "streaming": True,
            "frame": self._frame,
            "caption": caption,
            "prompt": scene.get("prompt", ""),
            "image_b64": base64.b64encode(png_bytes).decode("ascii"),
            "clarity": round(scene["clarity"], 3),
            "valence": round(float(packet.get("valence", 0)), 3),
            "arousal": round(float(packet.get("arousal", 0.3)), 3),
            "sources": list(dict.fromkeys(sources))[:6],
            "modality": modality,
            "involuntary": bool(involuntary),
            "label": f"imaginación: {caption[:48]}",
            "scene": {k: v for k, v in scene.items() if k not in ("prompt",)},
        }
        self.last = result
        self._history.insert(0, {"frame": self._frame, "caption": caption, "sources": result["sources"]})
        self._history = self._history[:STREAM_HISTORY]
        return result

    def maybe_imagine(
        self,
        brain: InfantApeBrain,
        *,
        thought: dict,
        vision: dict | None = None,
    ) -> dict | None:
        return self.advance_stream(brain, thought=thought, vision=vision)

    def _brain_sources(
        self,
        brain: InfantApeBrain,
        packet: dict,
        vision: dict | None,
    ) -> tuple[list[str], list[str]]:
        sources: list[str] = []
        fragments: list[str] = []

        wm = [w for w in (packet.get("working_memory") or []) if w][:4]
        if wm:
            sources.append("memoria de trabajo")
            fragments.extend(wm[:3])

        echo = packet.get("memory_echo")
        if echo:
            sources.append("hipocampo")
            fragments.append(str(echo)[:50])

        recent = brain.hippocampus.list_recent()[:4]
        for mem in recent:
            lbl = (mem.get("label") or mem.get("key") or "")[:45]
            if lbl and lbl not in fragments:
                if "hipocampo" not in sources:
                    sources.append("hipocampo")
                fragments.append(lbl)
                if len(fragments) >= 5:
                    break

        sem = sorted(
            brain.typed_memory.semantic.values(),
            key=lambda c: c.strength,
            reverse=True,
        )[:2]
        for concept in sem:
            if concept.label and concept.label not in fragments:
                sources.append("memoria semántica")
                fragments.append(concept.label[:40])

        if vision:
            fix = vision.get("fixation") or {}
            fix_label = fix.get("interpretation") or fix.get("label") or ""
            gist = vision.get("scene_gist") or ""
            if fix_label:
                sources.append("eco perceptual")
                fragments.append(fix_label[:40])
            elif gist:
                sources.append("eco perceptual")
                fragments.append(gist[:50])

        gist = packet.get("scene_gist")
        if gist and gist not in fragments:
            fragments.append(str(gist)[:50])

        room = packet.get("room") or brain.world.current_room()
        if not fragments:
            sources.append("default mode")
            fragments.append(f"espacio {room}")

        return sources, fragments[:6]

    def _involuntary_fragment(self, brain: InfantApeBrain, packet: dict) -> str | None:
        """Imágenes no solicitadas — más probables con arousal/estrés (Drubach 2007)."""
        arousal = float(packet.get("arousal", 0.3))
        pain = float((packet.get("pain") or {}).get("total", 0))
        rng = brain.random_streams.sensory if brain.random_streams is not None else np.random.default_rng(int(brain.seed + self._frame))
        p = 0.06 + arousal * 0.12 + pain * 0.15
        if rng.random() > p:
            return None
        recent = brain.hippocampus.list_recent()
        if not recent:
            return None
        pick = recent[int(rng.integers(0, min(3, len(recent))))]
        return (pick.get("label") or pick.get("key") or "")[:50] or None

    def _should_encode_neurally(self, scene: dict, clarity: float, assoc: float) -> bool:
        if self._frame - self._last_neural_frame < NEURAL_ENCODE_INTERVAL:
            return False
        salience = clarity + assoc * 0.35 + scene.get("clarity", 0) * 0.25
        if scene.get("involuntary"):
            salience += 0.15
        return salience > 0.38

    def _compose_scene(
        self,
        packet: dict,
        vision: dict | None,
        *,
        fragments: list[str],
        sources: list[str],
        frame: int,
        motor_act: float,
        clarity: float,
        assoc: float,
    ) -> dict[str, Any]:
        mood = packet.get("mood") or "calm"
        valence = float(packet.get("valence", 0))
        arousal = float(packet.get("arousal", 0.3))
        room = packet.get("room") or "casa"
        phase = (frame % 48) / 48.0

        anchor = fragments[0] if fragments else room
        prompt_parts = [f"Flujo interior en {room}."]
        if len(fragments) > 1:
            prompt_parts.append("Recombino: " + ", ".join(fragments[:3]) + ".")
        prompt = " ".join(prompt_parts)[:220]

        caption = anchor[:70]
        if len(fragments) > 1:
            caption = f"{fragments[0][:28]} · {fragments[1][:28]}"[:70]

        return {
            "mood": mood,
            "valence": valence,
            "arousal": arousal,
            "room": room,
            "anchor": anchor,
            "fragments": fragments,
            "sources": sources,
            "prompt": prompt,
            "caption": caption,
            "seed": _seed_from_parts(anchor, room, str(frame // 3)),
            "frame": frame,
            "phase": phase,
            "motor_act": motor_act,
            "assoc": assoc,
            "clarity": float(np.clip(clarity + assoc * 0.15, 0.22, 0.95)),
            "involuntary": "espontáneo" in sources,
        }

    def _render(self, scene: dict) -> bytes | None:
        try:
            from PIL import Image, ImageDraw, ImageFilter
        except ImportError:
            return None

        rng = np.random.default_rng(scene["seed"])
        w = h = IMG_SIZE
        phase = scene["phase"]
        c1, c2 = _mood_palette(scene["mood"], scene["valence"], scene["arousal"])
        img = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(img)

        for y in range(h):
            t = y / max(h - 1, 1)
            drift = math.sin(phase * math.tau + t * 2) * 0.08
            tt = t + drift
            tt = max(0, min(1, tt))
            r = int(c1[0] * (1 - tt) + c2[0] * tt)
            g = int(c1[1] * (1 - tt) + c2[1] * tt)
            b = int(c1[2] * (1 - tt) + c2[2] * tt)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        n_blobs = 3 + int(scene["arousal"] * 5)
        for i in range(n_blobs):
            cx = float((0.15 + 0.7 * ((i * 0.31 + phase) % 1.0)) * w)
            cy = float((0.12 + 0.76 * ((i * 0.47 + phase * 0.5) % 1.0)) * h)
            rad = float(rng.uniform(16, 42 + scene["arousal"] * 35))
            alpha = int(35 + scene["clarity"] * 75)
            color = (
                int(rng.integers(70, 255)),
                int(rng.integers(50, 220)),
                int(rng.integers(70, 255)),
            )
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(*color, alpha))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

        fx, fy = w * 0.5, h * 0.42
        glow_r = 24 + scene["clarity"] * 55
        for ring in range(3):
            r = glow_r + ring * 16 + math.sin(phase * math.tau) * 4
            alpha = int(85 - ring * 22)
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(255, 250, 220, alpha))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

        draw = ImageDraw.Draw(img)
        frags = scene.get("fragments") or []
        for i, frag in enumerate(frags[:5]):
            angle = (i / max(len(frags), 1)) * math.tau + phase * math.tau + scene["seed"] * 0.0003
            dist = 52 + i * 24 + math.sin(phase * math.tau + i) * 8
            x = fx + math.cos(angle) * dist
            y = fy + math.sin(angle) * dist
            sz = 7 + int(scene["clarity"] * 5)
            draw.ellipse([x - sz, y - sz, x + sz, y + sz], fill=(255, 255, 255, 200))
            if i == 0 and len(frag) < 22:
                draw.text((x - 20, y + sz + 2), frag[:18], fill=(255, 255, 240))

        if scene.get("motor_act", 0) > 0.35:
            for streak in range(int(3 + scene["motor_act"] * 5)):
                x0 = rng.uniform(0.1, 0.9) * w
                y0 = rng.uniform(0.2, 0.8) * h
                x1 = x0 + rng.uniform(-60, 60) * scene["motor_act"]
                y1 = y0 + rng.uniform(-40, 40) * scene["motor_act"]
                draw.line([(x0, y0), (x1, y1)], fill=(255, 220, 180), width=2)

        if scene.get("involuntary"):
            overlay = Image.new("RGBA", (w, h), (180, 40, 60, 28))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

        blur = max(0, int((1.0 - scene["clarity"]) * 3.5))
        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def snapshot(self) -> dict | None:
        if not self.last:
            return None
        return {k: v for k, v in self.last.items() if k != "image_b64"}
