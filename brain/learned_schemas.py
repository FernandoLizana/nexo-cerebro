"""
Schemas motores aprendidos por consolidación de éxitos.

Libre albedrío:
  - Los schemas aprendidos entran a la **competencia** PFC–striatum como los fijos.
  - Nunca fuerzan ``choice_key``; solo amplían el menú de opciones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Éxitos acumulados antes de consolidar un schema nuevo
DEFAULT_CONSOLIDATE_AFTER = 5
MAX_LEARNED = 24


@dataclass
class LearnedSchema:
    key: str
    label: str
    drive: str
    target: str
    parent_key: str
    successes: int = 0
    motor_affinity: list[int] = field(default_factory=list)
    rooms: list[str] = field(default_factory=list)
    consolidated: bool = False

    def as_action_schema(self) -> dict[str, str]:
        return {
            "key": self.key,
            "drive": self.drive,
            "label": self.label,
            "target": self.target,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "drive": self.drive,
            "target": self.target,
            "parent_key": self.parent_key,
            "successes": self.successes,
            "motor_affinity": list(self.motor_affinity),
            "rooms": list(self.rooms)[:8],
            "consolidated": self.consolidated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> LearnedSchema:
        return cls(
            key=str(d.get("key", "")),
            label=str(d.get("label", "")),
            drive=str(d.get("drive", "")),
            target=str(d.get("target", "")),
            parent_key=str(d.get("parent_key", "wander")),
            successes=int(d.get("successes", 0)),
            motor_affinity=[int(x) for x in (d.get("motor_affinity") or [])],
            rooms=[str(r) for r in (d.get("rooms") or [])],
            consolidated=bool(d.get("consolidated", False)),
        )


@dataclass
class SchemaLearner:
    """Acumula éxitos de patrones motor+contexto y consolida schemas nuevos."""

    consolidate_after: int = DEFAULT_CONSOLIDATE_AFTER
    candidates: dict[str, dict[str, Any]] = field(default_factory=dict)
    schemas: list[LearnedSchema] = field(default_factory=list)
    total_successes: int = 0
    consolidations: int = 0

    def active_schemas(self) -> list[dict[str, str]]:
        return [s.as_action_schema() for s in self.schemas if s.consolidated]

    def motor_affinity_for(self, key: str) -> list[int]:
        from .deliberation import MOTOR_AFFINITY

        for s in self.schemas:
            if s.key == key and s.motor_affinity:
                return list(s.motor_affinity)
        return list(MOTOR_AFFINITY.get(key, [0, 1]))

    def note_success(
        self,
        *,
        choice_key: str,
        room: str,
        motor: list[int] | None,
        dopamine: float = 0.5,
        confidence: float = 0.4,
    ) -> LearnedSchema | None:
        """
        Registra un acto exitoso. Si el fingerprint alcanza umbral, consolida.
        No escribe choice_key.
        """
        from .deliberation import ACTION_SCHEMAS, MOTOR_AFFINITY

        if not choice_key:
            return None
        if choice_key.startswith("learned_"):
            for s in self.schemas:
                if s.key == choice_key:
                    s.successes += 1
                    if room and room not in s.rooms:
                        s.rooms.append(room)
                    self.total_successes += 1
                    return None
            return None

        parent = next((s for s in ACTION_SCHEMAS if s["key"] == choice_key), None)
        if parent is None:
            return None

        motors = [int(m) for m in (motor or [])[:4]]
        mot_sig = ",".join(str(m) for m in motors[:2]) if motors else "-"
        fp = f"{room}|{choice_key}|{mot_sig}"
        cand = self.candidates.get(fp)
        if cand is None:
            cand = {
                "parent_key": choice_key,
                "room": room,
                "motor": motors,
                "count": 0,
                "drive": parent["drive"],
                "target": parent.get("target", ""),
                "label_base": parent["label"],
            }
            self.candidates[fp] = cand
        cand["count"] = int(cand["count"]) + 1
        if motors:
            cand["motor"] = motors
        boost = 1 if (dopamine > 0.55 and confidence > 0.5) else 0
        cand["count"] = int(cand["count"]) + boost
        self.total_successes += 1

        if int(cand["count"]) < self.consolidate_after:
            return None
        if len(self.schemas) >= MAX_LEARNED:
            return None

        key = f"learned_{room[:8]}_{choice_key}" if room else f"learned_{choice_key}"
        key = "".join(c if c.isalnum() or c == "_" else "_" for c in key)[:40]
        if any(s.key == key for s in self.schemas):
            for s in self.schemas:
                if s.key == key:
                    s.successes += 1
            return None

        label = f"{cand['label_base']} en {room}" if room else f"{cand['label_base']} (hábito)"
        affinity = motors[:3] if motors else list(MOTOR_AFFINITY.get(choice_key, [4, 1]))
        learned = LearnedSchema(
            key=key,
            label=label[:48],
            drive=str(cand["drive"]),
            target=str(cand.get("target") or ""),
            parent_key=choice_key,
            successes=int(cand["count"]),
            motor_affinity=affinity,
            rooms=[room] if room else [],
            consolidated=True,
        )
        self.schemas.append(learned)
        self.consolidations += 1
        return learned

    def note_affordance_success(
        self,
        *,
        candidate_key: str,
        object_type: str,
        dominant_drive: str = "",
        room: str = "",
        homeostasis_gain: float = 0.0,
        motor: list[int] | None = None,
    ) -> LearnedSchema | None:
        """
        Consolida schema desde éxito causal (objeto+acción), no desde forzar motor.
        Entra al menú PFC vía all_action_schemas; nunca escribe choice_key.
        """
        from .deliberation import ACTION_SCHEMAS, MOTOR_AFFINITY

        if not candidate_key or homeostasis_gain < 0.015:
            return None
        parent = next((s for s in ACTION_SCHEMAS if s["key"] == candidate_key), None)
        if parent is None:
            return None

        ot = "".join(c if c.isalnum() else "_" for c in (object_type or "obj"))[:12]
        fp = f"aff|{ot}|{candidate_key}|{room}"
        cand = self.candidates.get(fp)
        if cand is None:
            cand = {
                "parent_key": candidate_key,
                "room": room,
                "motor": list(motor or MOTOR_AFFINITY.get(candidate_key, [4])),
                "count": 0,
                "drive": dominant_drive or parent["drive"],
                "target": ot,
                "label_base": f"{parent['label']}·{ot}",
            }
            self.candidates[fp] = cand
        cand["count"] = int(cand["count"]) + 1
        self.total_successes += 1
        # Umbral más bajo que hábitos motores: evidencia causal es más informativa.
        need = max(2, self.consolidate_after // 2)
        if int(cand["count"]) < need:
            return None
        if len(self.schemas) >= MAX_LEARNED:
            return None

        key = f"learned_aff_{ot}_{candidate_key}"[:40]
        if any(s.key == key for s in self.schemas):
            for s in self.schemas:
                if s.key == key:
                    s.successes += 1
                    if room and room not in s.rooms:
                        s.rooms.append(room)
            return None

        affinity = list(cand.get("motor") or MOTOR_AFFINITY.get(candidate_key, [4, 1]))[:3]
        learned = LearnedSchema(
            key=key,
            label=str(cand["label_base"])[:48],
            drive=str(cand["drive"]),
            target=str(cand.get("target") or ot),
            parent_key=candidate_key,
            successes=int(cand["count"]),
            motor_affinity=affinity,
            rooms=[room] if room else [],
            consolidated=True,
        )
        self.schemas.append(learned)
        self.consolidations += 1
        return learned

    def to_dict(self) -> dict[str, Any]:
        return {
            "consolidate_after": self.consolidate_after,
            "total_successes": self.total_successes,
            "consolidations": self.consolidations,
            "n_schemas": len(self.schemas),
            "schemas": [s.to_dict() for s in self.schemas],
            "n_candidates": len(self.candidates),
            "agency_note": "Learned schemas compete in PFC contest; never force motor",
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> SchemaLearner:
        if not data:
            return cls()
        sl = cls(consolidate_after=int(data.get("consolidate_after", DEFAULT_CONSOLIDATE_AFTER)))
        sl.total_successes = int(data.get("total_successes", 0))
        sl.consolidations = int(data.get("consolidations", 0))
        sl.schemas = [LearnedSchema.from_dict(s) for s in (data.get("schemas") or [])]
        return sl


def all_action_schemas(brain) -> list[dict[str, str]]:
    """Schemas fijos + aprendidos consolidados (si flag ON)."""
    from .deliberation import ACTION_SCHEMAS
    from .experiment_flags import get_flags

    base = list(ACTION_SCHEMAS)
    if not get_flags(brain).enable_learned_schemas:
        return base
    learner = getattr(brain, "schema_learner", None)
    if learner is None:
        return base
    return base + learner.active_schemas()
