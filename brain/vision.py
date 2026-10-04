"""
Corteza visual: campo de visión, fóvea/periferia, interpretación de objetos visibles.

Simula ojos reales — solo se percibe lo que entra en el cono visual; la fóvea
aporta detalle, la periferia solo forma y saliencia.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .archetype_cards import card_key_from_meta, is_archetype_card_meta
from .world import World2D

FOVEA_HALF_RAD = 0.38
PERIPHERAL_HALF_RAD = 1.15

KIND_MEANING: dict[str, str] = {
    "book": "libro con páginas",
    "item": "objeto suelto",
    "sign": "señal o símbolo",
    "screen": "pantalla luminosa",
    "desk": "mesa de trabajo con cosas encima",
    "tv": "televisión",
    "fridge": "nevera — comida guardada",
    "bed": "cama para descansar",
    "sofa": "sofá blando",
    "door": "puerta al jardín",
    "bath": "bañera con agua",
    "toilet": "inodoro",
    "tree": "árbol del jardín",
    "crop": "cultivo maduro — se puede cosechar",
    "stove": "cocina — preparar comida",
    "companion": "figura viva — Nira",
    "offspring": "figura pequeña — hijo",
    "agent": "yo mismo",
}


def _wrap_angle(a: float) -> float:
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def _gaze_angle(agent_dir: int) -> float:
    """Dirección de la mirada en el plano 2D (0 = derecha)."""
    return 0.0 if agent_dir >= 0 else math.pi


@dataclass
class VisualPercept:
    id: str
    kind: str
    label: str
    distance: float
    angle_deg: float
    zone: str
    salience: float
    interpretation: str
    modality: str = "world"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "distance": round(self.distance, 1),
            "angle_deg": round(self.angle_deg, 1),
            "zone": self.zone,
            "salience": round(self.salience, 3),
            "interpretation": self.interpretation,
            "modality": self.modality,
        }


def _interpret(kind: str, label: str, *, distance: float, zone: str, meta: dict | None = None) -> str:
    meta = meta or {}
    if is_archetype_card_meta(meta):
        clean = label.replace("🃏", "").replace("◈", "").strip()
        if card_key_from_meta(meta):
            return f"carta de símbolo morada — {clean or label}"
        return f"símbolo en el escritorio: {clean or label}"
    base = KIND_MEANING.get(kind, kind)
    dist_word = "cerca" if distance < 45 else ("a media distancia" if distance < 85 else "lejos")
    detail = "nítido" if zone == "fovea" else "borroso en visión lateral"
    if label and label not in base:
        return f"{dist_word}, {detail}: {label} ({base})"
    return f"{dist_word}, {detail}: {base}"


def _fov_zone(delta: float) -> str | None:
    ad = abs(delta)
    if ad > PERIPHERAL_HALF_RAD:
        return None
    if ad <= FOVEA_HALF_RAD:
        return "fovea"
    return "peripheral"


def _entity_angle(ax: float, ay: float, ex: float, ey: float) -> float:
    return math.atan2(ey - ay, ex - ax)


def scan_world(
    world: World2D,
    *,
    companion: dict | None = None,
    offspring: dict | None = None,
    light_level: float = 1.0,
) -> dict[str, Any]:
    """Escaneo retinotópico del entorno desde la posición de Nexo."""
    ax, ay = world.agent_x, world.agent_y
    gaze = _gaze_angle(world.agent_dir)
    percepts: list[VisualPercept] = []

    def add_entity(
        *,
        eid: str,
        kind: str,
        label: str,
        ex: float,
        ey: float,
        modality: str = "world",
        meta: dict | None = None,
        salience_boost: float = 0.0,
    ) -> None:
        dist = float(math.hypot(ex - ax, ey - ay))
        if dist > world.view_radius * 1.35:
            return
        ang = _entity_angle(ax, ay, ex, ey)
        delta = _wrap_angle(ang - gaze)
        zone = _fov_zone(delta)
        if zone is None:
            return
        sal = salience_boost + (1.0 - dist / (world.view_radius * 1.4))
        if zone == "fovea":
            sal += 0.35
        if kind in ("companion", "tv") and world.tv_state.get("active") and kind == "tv":
            sal += 0.25
        if light_level < 0.35:
            sal *= 0.55 + 0.45 * light_level
        interp = _interpret(kind, label, distance=dist, zone=zone, meta=meta)
        percepts.append(
            VisualPercept(
                id=eid,
                kind=kind,
                label=label,
                distance=dist,
                angle_deg=math.degrees(delta),
                zone=zone,
                salience=float(np.clip(sal, 0, 1.5)),
                interpretation=interp,
                modality=modality,
            )
        )

    for obj in world.objects:
        add_entity(
            eid=obj.id,
            kind=obj.kind,
            label=obj.label,
            ex=obj.x,
            ey=obj.y,
            modality=obj.modality,
            meta=obj.meta,
            salience_boost=0.1 if obj.kind == "book" else 0.0,
        )

    for fu in world.furniture:
        if fu.kind == "door":
            continue
        cx, cy = fu.x + fu.w / 2, fu.y + fu.h / 2
        add_entity(eid=fu.id, kind=fu.kind, label=fu.label, ex=cx, ey=cy)

    if ax < 175:
        for i, t in enumerate(world.trees):
            add_entity(
                eid=f"tree-{i}",
                kind="tree",
                label="árbol",
                ex=float(t["x"]),
                ey=float(t["y"]),
            )

    if companion:
        add_entity(
            eid="companion",
            kind="companion",
            label=companion.get("name", "Nira"),
            ex=float(companion.get("x", ax + 60)),
            ey=float(companion.get("y", ay)),
            modality="social",
            salience_boost=0.3,
        )

    if offspring:
        add_entity(
            eid="offspring",
            kind="offspring",
            label=offspring.get("name", "Hijo"),
            ex=float(offspring.get("x", ax)),
            ey=float(offspring.get("y", ay)),
            modality="social",
            salience_boost=0.2,
        )

    percepts.sort(key=lambda p: -p.salience)
    fixation = percepts[0] if percepts else None
    foveal = [p for p in percepts if p.zone == "fovea"]
    peripheral = [p for p in percepts if p.zone == "peripheral"]

    scene_gist = _scene_gist(fixation, foveal, world, light_level)

    return {
        "gaze_dir": world.agent_dir,
        "gaze_deg": round(math.degrees(gaze), 1),
        "light_level": round(light_level, 3),
        "fixation": fixation.to_dict() if fixation else None,
        "foveal": [p.to_dict() for p in foveal[:6]],
        "peripheral": [p.to_dict() for p in peripheral[:8]],
        "count": len(percepts),
        "scene_gist": scene_gist,
        "percepts": [p.to_dict() for p in percepts[:12]],
    }


def _scene_gist(
    fixation: VisualPercept | None,
    foveal: list[VisualPercept],
    world: World2D,
    light_level: float,
) -> str:
    room = world.current_room()
    parts = [f"Estoy en {room}"]
    if light_level < 0.35:
        parts.append("casi no veo — poca luz")
    elif light_level < 0.6:
        parts.append("luz tenue")
    if fixation:
        parts.append(f"mi mirada cae en {fixation.interpretation}")
    elif foveal:
        parts.append(f"veo {foveal[0].interpretation}")
    else:
        parts.append("nada claro en el centro de la vista")
    others = [p.label or p.kind for p in foveal[1:3] if p.label or p.kind]
    if others:
        parts.append(f"también percibo {', '.join(others)}")
    if world.tv_state.get("active"):
        parts.append(f"la TV reproduce algo sobre {world.tv_state.get('title', '')[:30]}")
    if world.web_state.get("active"):
        parts.append(f"en el monitor veo búsqueda: {world.web_state.get('query', '')[:36]}")
    return ". ".join(parts) + "."


def encode_visual(percepts: list[dict], n: int) -> np.ndarray:
    """Vector retinal para corteza sensorial."""
    vec = np.zeros(min(n, 24), dtype=np.float32)
    for i, p in enumerate(percepts[:8]):
        base = i * 3
        if base + 2 >= vec.size:
            break
        vec[base] = float(np.clip(1.0 - p.get("distance", 100) / 140.0, 0, 1))
        vec[base + 1] = 1.0 if p.get("zone") == "fovea" else 0.45
        vec[base + 2] = float(p.get("salience", 0))
    m = float(vec.max())
    if m > 1e-6:
        vec /= m
    return vec


@dataclass
class SaccadeController:
    """Sacadas dirigidas por saliencia periférica — atención bottom-up ocular."""

    gaze_shift_deg: float = 0.0
    saccade_count: int = 0
    last_target: str = ""

    def apply(self, vision: dict, *, tick: int = 0) -> dict:
        if vision.get("headless"):
            return vision
        peripheral = list(vision.get("peripheral") or [])
        if not peripheral or tick % 16 != 0:
            return vision
        target = max(peripheral, key=lambda p: float(p.get("salience", 0)))
        if float(target.get("salience", 0)) < 0.5:
            return vision
        self.saccade_count += 1
        self.gaze_shift_deg = float(target.get("angle_deg", 0))
        self.last_target = str(target.get("label", target.get("id", "?")))[:40]
        foveal = list(vision.get("foveal") or [])
        promoted = dict(target)
        promoted["zone"] = "fovea"
        promoted["salience"] = float(np.clip(float(promoted.get("salience", 0)) + 0.2, 0, 1.5))
        foveal = [promoted] + [p for p in foveal if p.get("id") != promoted.get("id")][:5]
        vision["foveal"] = foveal
        vision["fixation"] = promoted
        vision["saccade"] = {
            "target": self.last_target,
            "shift_deg": round(self.gaze_shift_deg, 1),
            "count": self.saccade_count,
        }
        return vision


def enrich_depth_2_5d(vision: dict) -> dict:
    """Profundidad 2.5D — distancia + parallax por objeto visible."""
    depth_map: list[dict] = []
    seen: set[str] = set()
    for key in ("foveal", "peripheral", "percepts"):
        for p in vision.get(key) or []:
            pid = str(p.get("id", ""))
            if pid in seen:
                continue
            seen.add(pid)
            dist = float(p.get("distance", 80))
            depth_m = dist * 0.01
            parallax = float(np.clip(1.0 - dist / 130.0, 0, 1))
            p["depth_m"] = round(depth_m, 2)
            p["parallax"] = round(parallax, 3)
            depth_map.append({"id": pid, "depth_m": p["depth_m"], "parallax": p["parallax"]})
    depth_map.sort(key=lambda d: d["depth_m"])
    vision["depth_map"] = depth_map[:12]
    return vision
