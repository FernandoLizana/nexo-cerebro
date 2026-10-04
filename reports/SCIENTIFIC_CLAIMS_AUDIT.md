# Auditoría de afirmaciones científicas

**Fecha:** 2026-08-04

| Afirmación (original) | Ubicación | Clasificación | Evidencia actual | Reformulación sugerida |
|----------------------|-----------|---------------|------------------|------------------------|
| "libre albedrío" | `brain/agent_loop.py`, `deliberation.py`, docs | speculative | PFC elige `choice_key`; no fenomenología | proxy computacional de selección centralizada |
| "agency demostrada" | `docs/ARTEFACTO_ROADMAP_100_NEXO.md` | unsupported | Métricas internas, no validación externa | agency como proxy compuesto documentado |
| "100 mejoras validadas" | artefacto entrega | unsupported | Código + unit tests | 100 mejoras implementadas; evidencia variada por ítem |
| "61 passed" verificado | docs previos | partially supported | Subconjunto dynamics; suite=308 | citar corrida pytest real con commit |
| "consciencia demostrada" | conciencia workspace | hypothesis | Global workspace funcional | mecanismo funcional de acceso global |
| "cerebro humano completo" | README histórico | unsupported | Análogo parcial | arquitectura inspirada en motivos neurobiológicos |
| binding/spike ablación | E1 nobind CSV | partially supported | spike=0 mecanístico | usar tarea conductual `impulse_inhibition` |
| GPU validación biológica | docs GPU | unsupported | Acelera LIF | acelera simulación; no validación biológica |

## Política adoptada

Definición metodológica (README / KNOWN_LIMITATIONS):

> NEXO es una arquitectura cognitiva computacional modular, inspirada en motivos neurobiológicos, que integra percepción, memoria, afecto, deliberación, aprendizaje y selección de acciones mediante componentes funcionales y condiciones de ablación controladas. Sus métricas de agencia y consciencia son proxies computacionales y no constituyen evidencia de libre albedrío ni de consciencia fenomenológica.

## Acciones

- [x] `KNOWN_LIMITATIONS.md`
- [x] `legacy_agency_score` alias
- [ ] Moderación completa strings en `agent_loop.py` (pendiente — no silenciosa)
