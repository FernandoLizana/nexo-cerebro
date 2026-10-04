# P3 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P3 · **Veredicto:** PASS

## Resumen

NEXO ya no recibe una lista plana de todos los elementos web. Recibe una **escena perceptual limitada** por viewport, visibilidad, saliencia, oclusión y presupuesto de atención.

## Arquitectura

```text
BrowserSnapshot → PerceptionStrategy → PerceptualScene → AttentionGate → Actions → NEXO
```

## Evidencia

- 20 tests P3 PASS (`tests/test_p3_perception.py`)
- P2 browser 11/11 PASS (dom_fast default)
- P1 contract PASS
- v90 golden hash intacto: `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c`
- HYBRID ~0.9× DOM_FAST en snapshot simple (ver performance baseline)

## Modos

| Modo | Estado |
|------|--------|
| DOM_FAST | Baseline P2 |
| HYBRID | Principal P3 |
| VISION | NOT_IMPLEMENTED |

## Instalación

```bash
pip install -e ".[browser]"
playwright install chromium
pytest tests/test_p3_perception.py -m browser
```

## Artefactos

`artifacts/p3/preflight.json`, `artifacts/p3/quality_gate.json`

## Docs

`docs/cognitive_qa/P3_*.md`, ADR-0004

## P4

Semántica avanzada y calibración — ver `P3_HANDOFF_TO_P4.md`.
