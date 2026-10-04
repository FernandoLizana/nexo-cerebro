# H1 — Memoria imperfecta y promoción post-sueño

**Fecha:** 2026-08-08  
**Perfil:** `integrated_v80`  
**Hipótesis:** La memoria integrada puede promover episodios consolidados al almacén legacy sin fusión total, preservando imperfección y trazabilidad.

## Scripts

| Fase | Comando |
|------|---------|
| H1.0 headless | `python -m experiments.personal.run_h1_memory_day` |
| H1.1 interactivo 24h | `python -m experiments.personal.run_h1_memory_interactive` |
| H1.2 ablaciones | `python -m experiments.personal.run_h1_memory_comparison` |
| H1.3 retención | `python -m experiments.personal.run_h1_memory_retention` |

Artefactos: `results/personal/H1_memory/` (gitignored).

## Fix encoder (2026-08-08)

`HippocampalEncoderProcess` corre tras motor (priority 52) y empareja acción/recompensa del mismo tick.

## H1.1 — Interactivo 288 ticks (seed 42)

| Métrica | Valor |
|---------|-------|
| Episodios hippo | 64 |
| Consolidaciones | 15 |
| **Promociones → SQLite** | **15** |
| Legacy SQLite | 52 |
| Bridge parity (live) | 0.81 |

## H1.2 — Comparación ablaciones (288 ticks)

| Condición | Hippo | Promociones |
|-----------|-------|-------------|
| `integrated_full` | 64 | 15 |
| `abl_no_memory` | 0 | 0 |

## H1.3 — Retención tras delay + lesión (seed 42)

**Protocolo:** 288 ticks adquisición → 48 ticks delay → probe directo + 24 ticks runtime → lesión `lesion_sever_hippo_pfc` → probe `abl_no_memory`.

| Canal | Recall tras delay (n=15) | Tras ablación memoria |
|-------|--------------------------|------------------------|
| **HippocampalStore** (solo-hippo) | **0%** (episodios evicted del store; capacidad 64) | **0%** |
| **SQLite promovido** (`hippo_*`) | **80%** | **80%** |
| **Legacy nativo** (sin prefijo) | **100%** | **100%** |

### Interpretación H1.3

1. **Tres vías coexisten:** episodio integrado (volátil, capacidad 64), copia promovida en SQLite (`hippo_*`), y memoria legacy nativa del adapter.
2. **Delay 48 ticks:** el store hippo evicta episodios antiguos; el recall promovido en SQLite **persiste** (80%).
3. **`abl_no_memory`:** 0 eventos `memory.retrieved` en runtime; probe directo muestra que claves promovidas **sobreviven** la ablación (80%) — retención física en legacy.
4. **Imperfección:** 20% de promociones no recuperables tras delay (umbral/room/pattern drift) — comportamiento esperado.

## Conclusión hipótesis H1

La cadena **encode → consolidate → promote** es reproducible. La imperfección se preserva (pattern completion con ruido, umbral de confianza). La promoción no fusiona almacenes: añade trazas `hippo_{id}` auditables alongside legacy nativo.

## Próximo paso

**H2:** agency — certificado causal con `action.selected` válido bajo motor integrado; o Fase 15 producto/ciencia según arco.
