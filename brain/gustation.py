"""
Gustación y textura oral — comida, bebida y contacto con objetos blandos.

Sesga límbico/interocepción; no escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .encode import encode_text
from .material_qualities import furniture_qualities, object_qualities


@dataclass
class GustatoryPathway:
    last_taste: str = ""
    last_texture: str = ""
    sweetness: float = 0.0
    saltiness: float = 0.0
    umami: float = 0.0
    bitterness: float = 0.0
    texture_softness: float = 0.0

    def sample(
        self,
        brain,
        *,
        active_food: str | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        room = brain.world.current_room()
        label = active_food or ""
        softness = 0.2
        sweet = salt = umami = bitter = 0.0

        if not label and room == "cocina" and brain.body.hunger > 0.4:
            label = "aroma_comida_cocina"
            umami = 0.35
            salt = 0.15

        for fu in brain.world.furniture:
            if fu.kind in ("sofa", "bed") and brain.world._in_zone(fu.kind):
                q = furniture_qualities(
                    fu.kind,
                    room_temp=brain.world.room_temperature(),
                )
                softness = float(q.get("softness", 0.5))
                label = label or f"textura_{fu.kind}"
                break

        for obj in brain.world.objects:
            if obj.kind in ("crop", "food", "item") and obj.label:
                q = object_qualities(obj.kind, obj.meta)
                softness = float(q.get("softness", 0.3))
                if "fruta" in obj.label.lower() or obj.kind == "crop":
                    sweet = 0.55
                    label = obj.label
                elif "agua" in obj.label.lower():
                    salt = 0.05
                    label = obj.label
                else:
                    umami = 0.25
                    label = obj.label
                break

        self.last_taste = label or "neutro"
        self.last_texture = "blando" if softness > 0.45 else "firme"
        self.sweetness = sweet
        self.saltiness = salt
        self.umami = umami
        self.bitterness = bitter
        self.texture_softness = softness

        n = max(8, brain.n_sensory // 16)
        vec = encode_text(
            f"gusto:{label}|sweet{sweet:.2f}|salt{salt:.2f}|soft{softness:.2f}",
            n,
        ).astype(np.float32)
        vec *= float(np.clip(0.25 + sweet + salt + umami + softness * 0.3, 0.15, 1.0))

        meta = {
            "taste": self.last_taste,
            "texture": self.last_texture,
            "sweetness": round(sweet, 3),
            "saltiness": round(salt, 3),
            "umami": round(umami, 3),
            "softness": round(softness, 3),
        }
        return vec, meta

    def note_intake(self, *, label: str, sweetness: float = 0.0, saltiness: float = 0.0) -> None:
        self.last_taste = label[:60]
        self.sweetness = float(np.clip(sweetness, 0, 1))
        self.saltiness = float(np.clip(saltiness, 0, 1))

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_taste": self.last_taste,
            "texture": self.last_texture,
            "sweetness": round(self.sweetness, 3),
            "saltiness": round(self.saltiness, 3),
            "umami": round(self.umami, 3),
            "softness": round(self.texture_softness, 3),
        }
