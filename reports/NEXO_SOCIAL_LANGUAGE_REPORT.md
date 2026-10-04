# NEXO Sprint 8 — Cognición social y lenguaje

## Alcance implementado

- **Social (`nexo/social/`)**: modelo del cuidador, confianza, apego; ToM simplificada con sesgo de acción social.
- **Lenguaje (`nexo/language/`)**: compositor neural por plantillas (sin LLM) — verbaliza hambre, duda, contacto social, etc.
- **Procesos (`nexo/core/process_social.py`)**:
  - `SocialModelProcess` (69) — percepción social del cuidador
  - `TheoryOfMindProcess` (68) — inferencia de creencias del otro
  - `SocialExchangeProcess` (50) — turno social tras `approach_caregiver`
  - `LanguageProductionProcess` (49) — enunciados desde estado interno
- **Runtime**: `social_mode: legacy | integrated` y perfil `configs/nexo/integrated_v8.yaml`.

## Pipeline social (modo integrated)

```text
SocialModel → ToM → … → motor → SocialExchange → LanguageProduction
```

El sesgo ToM (`social_action_bias`) se inyecta en PFC/BG junto al workspace.

## Eventos nuevos

| Evento | Rol |
|--------|-----|
| `social.perceived` | Estado del cuidador |
| `social.tom_inferred` | Creencia inferida + sesgo |
| `social.exchange` | Turno agente ↔ cuidador |
| `language.produced` | Enunciado generado |

## Verificación

```powershell
python -m pytest tests/test_social_integrated.py tests/test_consciousness_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v8.yaml
```

## Limitaciones honestas

- Lenguaje por plantillas, no LLM ni RAG tutor.
- ToM heurística (no simulación mental completa).
- Un solo agente social (cuidador) en RoomWorld.
- Sin vergüenza social ni diálogo multi-agente completo.

## Próximo sprint sugerido

Sprint 9: sueño, consolidación mnésica y desarrollo.
