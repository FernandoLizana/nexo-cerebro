"""Load persona definitions from YAML configs."""

from __future__ import annotations

from pathlib import Path

import yaml

from nexo_qa.personas.models import SCHEMA_VERSION, CognitivePersona, PersonaTraits
from nexo_qa.personas.validation import validate_traits

PERSONAS_DIR = Path(__file__).resolve().parents[2] / "configs" / "nexo_qa" / "personas"


def load_persona(path: Path | str) -> CognitivePersona:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    traits_raw = dict(data.get("traits") or data)
    persona_id = str(data.get("persona_id") or path.stem)
    errors = validate_traits(traits_raw)
    if errors:
        raise ValueError(f"{persona_id}: {'; '.join(errors)}")
    return CognitivePersona(
        persona_id=persona_id,
        schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        traits=PersonaTraits.from_mapping(traits_raw),
        description=str(data.get("description", "")),
        metadata=dict(data.get("metadata") or {}),
    )


def load_preset(name: str) -> CognitivePersona:
    path = PERSONAS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    return load_persona(path)


def list_presets() -> tuple[str, ...]:
    if not PERSONAS_DIR.exists():
        return ()
    return tuple(p.stem for p in sorted(PERSONAS_DIR.glob("*.yaml")))
