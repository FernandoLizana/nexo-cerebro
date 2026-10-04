# P2 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P2 · **Veredicto:** PASS

## Resumen

NEXO interactúa con una **web real local** usando el **mismo Cognitive Core** que LegacyWorld y MockWorld. Playwright queda encapsulado en `nexo_qa/browser/`. El core no importa Playwright ni recibe selectores.

## Arquitectura

```text
IntegratedRuntime → EnvironmentProtocol → BrowserWorld → PlaywrightDriver → Chromium → Web Lab
```

## Evidencia

- 11 tests browser PASS
- `test_three_worlds_one_brain` PASS
- v90 golden hash intacto
- P1 tests 26/26 PASS
- `import nexo` no requiere Playwright

## Primer loop web (seed 42, 64 ticks)

- NEXO navegó a `name.html` tras `activate "Comenzar"`
- 64 decisiones integradas, certificados causales y agency audit activos
- **No** se entregó script de pasos al runtime
- Objetivo Pro no garantizado (`P2_LIMITATION_GOAL_SEMANTICS`)

## Instalación browser

```bash
pip install -e ".[browser]"
playwright install chromium
pytest tests/test_p2_browser.py -m browser
```

## Artefactos

`artifacts/p2/` · docs `docs/cognitive_qa/P2_*.md` · ADR-0003

## P3

Mejorar percepción (salience, HYBRID/VISION) sin reescribir el contrato P1.
