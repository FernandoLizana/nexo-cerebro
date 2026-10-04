# P5 — Persona Model

## CognitivePersona

```python
CognitivePersona(
  persona_id: str,
  schema_version: int,
  traits: PersonaTraits,
  description: str,
)
```

## Serialization

YAML under `configs/nexo_qa/personas/*.yaml`:

```yaml
schema_version: 1
persona_id: low_wm
traits:
  working_memory_capacity: 2
  distractibility: 0.55
  ...
```

## Identity

- `persona_id` — stable identifier
- `schema_version` — currently `1`
- `config_hash()` — SHA256 prefix of traits JSON

## Validation

`validate_traits()` rejects NaN, negative WM capacity, unknown fields (strict), out-of-range floats.

## Audit

`PersonaApplicationReport` records requested vs effective values per mapping.
