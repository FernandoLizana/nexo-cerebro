# NEXO Sprint 7 — Workspace global y metacognición

## Alcance implementado

- **Workspace global (`nexo/workspace/`)**: competencia por acceso consciente (capacidad 3), sesgo de acción hacia PFC/BG.
- **Metacognición (`nexo/metacognition/`)**: claridad, duda, confianza, agencia y estado fenomenológico funcional (`claro`, `difuso`, `dividido`, etc.).
- **Procesos (`nexo/core/process_consciousness.py`)**:
  - `GlobalWorkspaceProcess` (prioridad 67)
  - `MetacognitionProcess` (prioridad 64)
- **Runtime**: `consciousness_mode: legacy | integrated` y perfil `configs/nexo/integrated_v7.yaml`.

## Pipeline consciencia (modo integrated)

```text
Percepción → GlobalWorkspace (broadcast) → Metacognición → WM → PFC → BG …
```

El sesgo del workspace se inyecta en deliberación PFC y ganglios basales vía `workspace_action_bias`.

## Eventos nuevos

| Evento | Rol |
|--------|-----|
| `workspace.broadcast` | Contenido consciente global (ya existía reducer) |
| `metacognition.updated` | Snapshot claridad/duda/agencia |

## Verificación

```powershell
python -m pytest tests/test_consciousness_integrated.py tests/test_learning_integrated.py tests/test_executive_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v7.yaml
```

## Limitaciones honestas

- No hay self-model narrativo completo ni reportabilidad lingüística.
- Metacognición usa señales heurísticas, no calibración empírica humana.
- Workspace limitado a RoomWorld (6 acciones, 4 modalidades).
- No se afirma fenomenología ni qualia.

## Próximo sprint sugerido

Sprint 8: cognición social y lenguaje.
