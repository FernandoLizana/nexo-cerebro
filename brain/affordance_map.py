"""
Affordances aprendidas: objeto + interacción + contexto → consecuencias observadas.

Agency:
  - Este módulo nunca escribe ``choice_key`` ni llama al motor.
  - Solo produce evidencia Go/No-Go acotada para concursantes ya creados por PFC.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

AFFORDANCE_SCHEMA_VERSION = 1
AFFORDANCE_BIAS_MAX = 0.08
CONFIDENCE_EXPERIENCE_K = 4.0
SUCCESS_GAIN_THRESHOLD = 0.015

HOMEOSTATIC_FIELDS: tuple[str, ...] = (
    "hunger",
    "thirst",
    "fatigue",
    "comfort",
    "bladder",
    "hygiene",
    "pain",
    "pleasure",
)

DRIVE_GAIN_FIELD: dict[str, tuple[str, float]] = {
    "seek_food": ("hunger", -1.0),
    "seek_water": ("thirst", -1.0),
    "seek_rest": ("fatigue", -1.0),
    "sleep_need": ("fatigue", -1.0),
    "seek_relief": ("pain", -1.0),
    "seek_bathroom": ("bladder", -1.0),
    "seek_hygiene": ("hygiene", -1.0),
    "seek_comfort": ("comfort", 1.0),
}

EVENT_CANDIDATE_KEYS: dict[str, str] = {
    "drink": "drink",
    "eat": "eat",
    "eat_cooked": "eat",
    "harvest": "harvest",
    "cook": "cook",
    "rest": "rest",
    "bathe": "hygiene",
    "bathroom": "bathroom",
    "tv_use": "tv",
}

EVENT_OBJECT_TYPES: dict[str, str] = {
    "drink": "fountain",
    "eat": "fridge",
    "eat_cooked": "food_source",
    "harvest": "crop",
    "cook": "stove",
    "rest": "bed",
    "bathe": "bath",
    "bathroom": "toilet",
    "tv_use": "tv",
}


def body_snapshot(body: Any) -> dict[str, float]:
    """Captura mínima serializable antes/después de una consecuencia."""
    return {
        "hunger": float(getattr(body, "hunger", 0.0)),
        "thirst": float(getattr(body, "thirst", 0.0)),
        "fatigue": float(getattr(body, "fatigue", 0.0)),
        "comfort": float(getattr(body, "comfort", 0.0)),
        "bladder": float(getattr(body, "bladder", 0.0)),
        "hygiene": float(getattr(body, "hygiene", 0.0)),
        "pain": float(body.total_pain()) if hasattr(body, "total_pain") else 0.0,
        "pleasure": float(getattr(body, "pleasure", 0.0)),
    }


def observed_outcomes(
    before: dict[str, float], after: dict[str, float]
) -> dict[str, float]:
    return {
        name: float(after.get(name, 0.0) - before.get(name, 0.0))
        for name in HOMEOSTATIC_FIELDS
    }


def homeostasis_gain(outcomes: dict[str, float], dominant_drive: str) -> float:
    """Ganancia firmada para la necesidad dominante."""
    field_sign = DRIVE_GAIN_FIELD.get(dominant_drive)
    if field_sign:
        name, sign = field_sign
        return float(sign * outcomes.get(name, 0.0))
    # Fallback conservador: alivios de necesidad + confort/placer.
    return float(
        -0.24 * outcomes.get("hunger", 0.0)
        - 0.24 * outcomes.get("thirst", 0.0)
        - 0.16 * outcomes.get("fatigue", 0.0)
        - 0.12 * outcomes.get("pain", 0.0)
        - 0.08 * outcomes.get("bladder", 0.0)
        - 0.06 * outcomes.get("hygiene", 0.0)
        + 0.06 * outcomes.get("comfort", 0.0)
        + 0.04 * outcomes.get("pleasure", 0.0)
    )


def event_identity(event: dict[str, Any]) -> tuple[str, str, str, str] | None:
    """
    Retorna (object_type, object_id, interaction, candidate_key).
    Los eventos narrativos/movimiento no generan affordances.
    """
    interaction = str(event.get("type", "")).strip()
    candidate_key = EVENT_CANDIDATE_KEYS.get(interaction)
    if not candidate_key:
        return None
    object_type = str(
        event.get("object_type")
        or EVENT_OBJECT_TYPES.get(interaction)
        or event.get("target")
        or "unknown"
    )
    object_id = str(event.get("object_id") or event.get("target") or object_type)
    return object_type, object_id, interaction, candidate_key


@dataclass
class AffordanceEvidence:
    candidate_key: str
    drive_key: str
    expected_homeostasis_gain: float
    confidence: float
    uncertainty: float
    source_object: str
    object_type: str
    bias: float
    observations: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_key": self.candidate_key,
            "drive_key": self.drive_key,
            "expected_homeostasis_gain": round(self.expected_homeostasis_gain, 4),
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "source_object": self.source_object,
            "object_type": self.object_type,
            "bias": round(self.bias, 4),
            "observations": self.observations,
        }


@dataclass
class AffordanceRecord:
    object_type: str
    object_id: str
    interaction: str
    candidate_key: str
    dominant_drive: str
    room: str
    expected_outcomes: dict[str, float] = field(default_factory=dict)
    mean_homeostasis_gain: float = 0.0
    observation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    mean_prediction_error: float = 0.0
    rooms_seen: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return "|".join(
            (
                self.object_type,
                self.object_id,
                self.interaction,
                self.candidate_key,
                self.dominant_drive,
            )
        )

    @property
    def confidence(self) -> float:
        if self.observation_count <= 0:
            return 0.0
        success_rate = self.success_count / self.observation_count
        experience = 1.0 - math.exp(
            -self.observation_count / CONFIDENCE_EXPERIENCE_K
        )
        consistency = 1.0 / (1.0 + 4.0 * self.mean_prediction_error)
        return float(max(0.0, min(1.0, success_rate * experience * consistency)))

    def update(self, outcomes: dict[str, float], gain: float, room: str) -> None:
        old_count = self.observation_count
        if old_count:
            error = sum(
                abs(float(outcomes.get(k, 0.0)) - float(self.expected_outcomes.get(k, 0.0)))
                for k in HOMEOSTATIC_FIELDS
            ) / len(HOMEOSTATIC_FIELDS)
            self.mean_prediction_error = float(
                (self.mean_prediction_error * old_count + error) / (old_count + 1)
            )
        self.observation_count += 1
        n = self.observation_count
        for name in HOMEOSTATIC_FIELDS:
            old = float(self.expected_outcomes.get(name, 0.0))
            self.expected_outcomes[name] = float(
                old + (float(outcomes.get(name, 0.0)) - old) / n
            )
        self.mean_homeostasis_gain = float(
            self.mean_homeostasis_gain + (gain - self.mean_homeostasis_gain) / n
        )
        if gain >= SUCCESS_GAIN_THRESHOLD:
            self.success_count += 1
        else:
            self.failure_count += 1
        if room and room not in self.rooms_seen:
            self.rooms_seen.append(room)
            self.rooms_seen = self.rooms_seen[-8:]

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "interaction": self.interaction,
            "candidate_key": self.candidate_key,
            "dominant_drive": self.dominant_drive,
            "room": self.room,
            "expected_outcomes": {
                k: round(float(v), 6) for k, v in self.expected_outcomes.items()
            },
            "mean_homeostasis_gain": round(self.mean_homeostasis_gain, 6),
            "observation_count": self.observation_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "mean_prediction_error": round(self.mean_prediction_error, 6),
            "confidence": round(self.confidence, 6),
            "rooms_seen": self.rooms_seen,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AffordanceRecord:
        return cls(
            object_type=str(data.get("object_type", "unknown")),
            object_id=str(data.get("object_id", "unknown")),
            interaction=str(data.get("interaction", "interact")),
            candidate_key=str(data.get("candidate_key", "wander")),
            dominant_drive=str(data.get("dominant_drive", "")),
            room=str(data.get("room", "")),
            expected_outcomes={
                str(k): float(v)
                for k, v in dict(data.get("expected_outcomes") or {}).items()
            },
            mean_homeostasis_gain=float(data.get("mean_homeostasis_gain", 0.0)),
            observation_count=int(data.get("observation_count", 0)),
            success_count=int(data.get("success_count", 0)),
            failure_count=int(data.get("failure_count", 0)),
            mean_prediction_error=float(data.get("mean_prediction_error", 0.0)),
            rooms_seen=[str(x) for x in (data.get("rooms_seen") or [])],
        )


@dataclass
class AffordanceMap:
    records: dict[str, AffordanceRecord] = field(default_factory=dict)
    last_evidence: list[AffordanceEvidence] = field(default_factory=list)
    last_observation: dict[str, Any] | None = None
    load_error: str = ""
    save_error: str = ""
    _path: Path | None = field(default=None, init=False, repr=False)

    def bind_state_dir(self, state_dir: Path) -> None:
        self._path = Path(state_dir) / "affordances.json"
        self.load()

    def observe(
        self,
        *,
        event: dict[str, Any],
        before: dict[str, float],
        after: dict[str, float],
        dominant_drive: str,
        room: str,
        decision_key: str = "",
    ) -> AffordanceRecord | None:
        identity = event_identity(event)
        if identity is None:
            return None
        object_type, object_id, interaction, candidate_key = identity
        outcomes = observed_outcomes(before, after)
        gain = homeostasis_gain(outcomes, dominant_drive)
        probe = AffordanceRecord(
            object_type=object_type,
            object_id=object_id,
            interaction=interaction,
            candidate_key=candidate_key,
            dominant_drive=dominant_drive,
            room=room,
        )
        record = self.records.get(probe.key)
        if record is None:
            record = probe
            self.records[record.key] = record
        record.update(outcomes, gain, room)
        self.last_observation = {
            "record_key": record.key,
            "decision_key": decision_key,
            "candidate_key": candidate_key,
            "event_type": interaction,
            "object_type": object_type,
            "object_id": object_id,
            "dominant_drive": dominant_drive,
            "room": room,
            "outcomes": {k: round(v, 5) for k, v in outcomes.items()},
            "homeostasis_gain": round(gain, 5),
            "confidence": round(record.confidence, 5),
        }
        return record

    def evidence_for(
        self,
        *,
        candidate_keys: list[str],
        dominant_drive: str,
        room: str,
    ) -> list[AffordanceEvidence]:
        allowed = set(candidate_keys)
        best: dict[str, AffordanceEvidence] = {}
        for record in self.records.values():
            if record.candidate_key not in allowed:
                continue
            if record.dominant_drive and dominant_drive:
                if record.dominant_drive != dominant_drive:
                    continue
            context_scale = 1.0 if room in record.rooms_seen or room == record.room else 0.85
            raw = record.mean_homeostasis_gain * record.confidence * context_scale
            bias = float(max(-AFFORDANCE_BIAS_MAX, min(AFFORDANCE_BIAS_MAX, raw)))
            evidence = AffordanceEvidence(
                candidate_key=record.candidate_key,
                drive_key=record.dominant_drive,
                expected_homeostasis_gain=record.mean_homeostasis_gain,
                confidence=record.confidence,
                uncertainty=1.0 - record.confidence,
                source_object=record.object_id,
                object_type=record.object_type,
                bias=bias,
                observations=record.observation_count,
            )
            current = best.get(evidence.candidate_key)
            if current is None or abs(evidence.bias) > abs(current.bias):
                best[evidence.candidate_key] = evidence
        self.last_evidence = sorted(
            best.values(), key=lambda e: abs(e.bias), reverse=True
        )
        return self.last_evidence

    def consolidate_during_sleep(self) -> dict[str, Any]:
        """
        Sueño: refuerza registros fiables y poda los crónicamente fallidos.
        No escribe choice_key ni ejecuta motor.
        """
        reinforced = 0
        pruned = 0
        to_delete: list[str] = []
        for key, record in self.records.items():
            if record.observation_count <= 0:
                continue
            success_rate = record.success_count / max(1, record.observation_count)
            if success_rate >= 0.6 and record.observation_count >= 2:
                # baja el error medio → sube confianza efectiva
                record.mean_prediction_error = float(
                    max(0.0, record.mean_prediction_error * 0.88)
                )
                reinforced += 1
            if (
                record.observation_count >= 3
                and success_rate < 0.28
                and record.confidence < 0.18
            ):
                to_delete.append(key)
        for key in to_delete:
            self.records.pop(key, None)
            pruned += 1
        if reinforced or pruned:
            self.save()
        return {
            "reinforced": reinforced,
            "pruned": pruned,
            "remaining": len(self.records),
            "agency_note": "Sleep edits affordance memory only; PFC still selects actions",
        }

    def biases_for(
        self,
        *,
        candidate_keys: list[str],
        dominant_drive: str,
        room: str,
    ) -> dict[str, float]:
        return {
            evidence.candidate_key: evidence.bias
            for evidence in self.evidence_for(
                candidate_keys=candidate_keys,
                dominant_drive=dominant_drive,
                room=room,
            )
            if abs(evidence.bias) > 1e-6
        }

    def save(self) -> bool:
        if self._path is None:
            return False
        payload = {
            "schema_version": AFFORDANCE_SCHEMA_VERSION,
            "records": [record.to_dict() for record in self.records.values()],
        }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            tmp.replace(self._path)
            self.save_error = ""
            return True
        except (OSError, TypeError, ValueError) as exc:
            self.save_error = f"{type(exc).__name__}: {exc}"
            return False

    def load(self) -> bool:
        self.load_error = ""
        if self._path is None or not self._path.is_file():
            return False
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            rows = payload.get("records") or []
            loaded: dict[str, AffordanceRecord] = {}
            for row in rows:
                record = AffordanceRecord.from_dict(row)
                loaded[record.key] = record
            self.records = loaded
            return True
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
            self.records = {}
            self.load_error = f"{type(exc).__name__}: {exc}"
            return False

    def clear(self) -> None:
        self.records.clear()
        self.last_evidence.clear()
        self.last_observation = None

    def to_dict(self) -> dict[str, Any]:
        ranked = sorted(
            self.records.values(),
            key=lambda record: (record.confidence, record.observation_count),
            reverse=True,
        )
        return {
            "schema_version": AFFORDANCE_SCHEMA_VERSION,
            "record_count": len(self.records),
            "records": [record.to_dict() for record in ranked[:32]],
            "last_evidence": [e.to_dict() for e in self.last_evidence[:8]],
            "last_biases": {
                e.candidate_key: round(e.bias, 4) for e in self.last_evidence[:8]
            },
            "last_observation": self.last_observation,
            "bias_max": AFFORDANCE_BIAS_MAX,
            "load_error": self.load_error or None,
            "save_error": self.save_error or None,
            "agency_note": "Affordances provide bounded evidence; PFC selects choice_key",
        }
