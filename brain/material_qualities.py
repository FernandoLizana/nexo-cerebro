"""
Cualidades físicas de muebles y objetos — temperatura, textura, tacto.

Sincronizado con el renderer 3D (game3d.js / material_qualities.js).
"""

from __future__ import annotations

from typing import Any

from .archetype_cards import is_archetype_card_meta

# kind → propiedades base (°C superficie a ~20°C ambiente)
_FURNITURE_BASE: dict[str, dict[str, Any]] = {
    "desk": {
        "texture": "roble",
        "material": "madera",
        "temperature_c": 19.5,
        "roughness": 0.82,
        "metalness": 0.04,
        "softness": 0.12,
        "hardness": 0.78,
        "conductivity": 0.15,
        "porosity": 0.35,
    },
    "tv": {
        "texture": "plástico mate",
        "material": "electrónica",
        "temperature_c": 22.0,
        "roughness": 0.45,
        "metalness": 0.12,
        "softness": 0.05,
        "hardness": 0.65,
        "conductivity": 0.08,
        "porosity": 0.02,
    },
    "fridge": {
        "texture": "acero cepillado",
        "material": "metal",
        "temperature_c": 8.0,
        "roughness": 0.38,
        "metalness": 0.72,
        "softness": 0.02,
        "hardness": 0.92,
        "conductivity": 0.55,
        "porosity": 0.0,
    },
    "fountain": {
        "texture": "piedra húmeda",
        "material": "piedra",
        "temperature_c": 16.0,
        "roughness": 0.7,
        "metalness": 0.05,
        "softness": 0.08,
        "hardness": 0.85,
        "conductivity": 0.35,
        "porosity": 0.2,
    },
    "food_bowl": {
        "texture": "cerámica",
        "material": "cerámica",
        "temperature_c": 18.5,
        "roughness": 0.55,
        "metalness": 0.02,
        "softness": 0.1,
        "hardness": 0.7,
        "conductivity": 0.2,
        "porosity": 0.08,
    },
    "bed": {
        "texture": "algodón",
        "material": "textil",
        "temperature_c": 21.0,
        "roughness": 0.94,
        "metalness": 0.0,
        "softness": 0.88,
        "hardness": 0.15,
        "conductivity": 0.04,
        "porosity": 0.72,
    },
    "sofa": {
        "texture": "terciopelo",
        "material": "textil",
        "temperature_c": 20.5,
        "roughness": 0.91,
        "metalness": 0.0,
        "softness": 0.82,
        "hardness": 0.22,
        "conductivity": 0.05,
        "porosity": 0.68,
    },
    "bath": {
        "texture": "porcelana",
        "material": "cerámica",
        "temperature_c": 18.0,
        "roughness": 0.22,
        "metalness": 0.08,
        "softness": 0.08,
        "hardness": 0.85,
        "conductivity": 0.25,
        "porosity": 0.01,
    },
    "toilet": {
        "texture": "porcelana sanitaria",
        "material": "cerámica",
        "temperature_c": 17.5,
        "roughness": 0.28,
        "metalness": 0.06,
        "softness": 0.06,
        "hardness": 0.88,
        "conductivity": 0.22,
        "porosity": 0.01,
    },
    "stove": {
        "texture": "hierro fundido",
        "material": "metal",
        "temperature_c": 24.0,
        "roughness": 0.55,
        "metalness": 0.65,
        "softness": 0.01,
        "hardness": 0.95,
        "conductivity": 0.72,
        "porosity": 0.0,
    },
    "door": {
        "texture": "madera pintada",
        "material": "madera",
        "temperature_c": 19.0,
        "roughness": 0.75,
        "metalness": 0.05,
        "softness": 0.15,
        "hardness": 0.7,
        "conductivity": 0.12,
        "porosity": 0.28,
    },
}

_OBJECT_BASE: dict[str, dict[str, Any]] = {
    "book": {
        "texture": "papel encuadernado",
        "material": "papel",
        "temperature_c": 20.0,
        "roughness": 0.88,
        "metalness": 0.0,
        "softness": 0.35,
    },
    "crop": {
        "texture": "orgánico",
        "material": "vegetal",
        "temperature_c": 16.0,
        "roughness": 0.85,
        "metalness": 0.0,
        "softness": 0.55,
    },
    "tree": {
        "texture": "corteza",
        "material": "madera viva",
        "temperature_c": 15.0,
        "roughness": 0.9,
        "metalness": 0.0,
        "softness": 0.4,
    },
}


def _merge(base: dict, extra: dict) -> dict[str, Any]:
    out = dict(base)
    out.update(extra)
    return out


def furniture_qualities(
    kind: str,
    *,
    room_temp: float = 20.0,
    tv_active: bool = False,
    web_active: bool = False,
    stove_hot: bool = False,
) -> dict[str, Any]:
    base = dict(_FURNITURE_BASE.get(kind, _FURNITURE_BASE["desk"]))
    q = _merge(base, {"kind": kind, "ambient_c": round(room_temp, 1)})

    if kind == "fridge":
        q["temperature_c"] = round(4.0 + room_temp * 0.05, 1)
        q["feels"] = "frío al tacto"
    elif kind == "stove" and stove_hot:
        q["temperature_c"] = 85.0
        q["feels"] = "caliente — precaución"
        q["emissive"] = True
    elif kind == "bath":
        q["temperature_c"] = round(18.0 + (room_temp - 20) * 0.3, 1)
        q["feels"] = "cerámica húmeda"
    elif kind == "sofa":
        q["temperature_c"] = round(room_temp + 0.8, 1)
        q["feels"] = "acogedor"
    elif kind == "bed":
        q["feels"] = "suave y cálido"
    elif kind == "tv" and tv_active:
        q["temperature_c"] = 28.0
        q["feels"] = "emite calor leve"
        q["emissive"] = True
    elif kind == "desk" and web_active:
        q["temperature_c"] = 24.0
        q["feels"] = "pantalla activa"
        q["emissive"] = True
    else:
        q["feels"] = _default_feel(q)

    q["temperature_c"] = round(float(q["temperature_c"]), 1)
    return q


def object_qualities(kind: str, meta: dict | None = None) -> dict[str, Any]:
    meta = meta or {}
    if kind == "crop" and meta.get("food"):
        base = dict(_OBJECT_BASE["crop"])
        base["label_food"] = str(meta.get("food", ""))
        base["temperature_c"] = 14.0 if meta.get("ripe", True) else 16.0
        base["feels"] = "fresco del jardín" if meta.get("ripe", True) else "tierno"
        return _merge(base, {"kind": kind})
    if is_archetype_card_meta(meta):
        return {
            "kind": kind,
            "texture": "cartulina mate",
            "material": "papel",
            "temperature_c": 20.0,
            "roughness": 0.72,
            "metalness": 0.05,
            "softness": 0.4,
            "feels": "misterioso al tacto",
        }
    base = dict(_OBJECT_BASE.get(kind, _OBJECT_BASE["book"]))
    base["feels"] = _default_feel(base)
    return _merge(base, {"kind": kind})


def _default_feel(q: dict) -> str:
    t = float(q.get("temperature_c", 20))
    if t < 10:
        return "frío"
    if t > 35:
        return "caliente"
    s = float(q.get("softness", 0.3))
    if s > 0.7:
        return "blando"
    if float(q.get("hardness", 0.5)) > 0.8:
        return "duro"
    return "neutro"
