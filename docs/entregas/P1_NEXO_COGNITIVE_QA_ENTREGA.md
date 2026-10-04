# P1 — NEXO Cognitive QA · artefacto de entrega

**Fecha:** 2026-08-19  
**Baseline científico:** `integrated_v90`  
**P0 freeze:** `d64b70f8` · golden hash `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c`  
**Python:** 3.11 · Windows

Este archivo es el handoff autosuficiente para P2. Leer también `docs/cognitive_qa/P1_HANDOFF_TO_P2.md`.

P1 **no implementa un navegador**. P1 desacopla acciones y el contrato agente↔mundo.

---

## 1. Resumen ejecutivo

El Cognitive Core ya no necesita una lista fija de verbos de RoomWorld para deliberar. El entorno entrega `ActionSchema[]`; PFC puntúa affordances; el mundo ejecuta el `id`.

Evidencia:

- **RoomWorld** y **MockWorld** corren el **mismo** `IntegratedRuntime` (`test_two_worlds_one_brain`).
- Golden v90 **idéntico** (STRICT).
- MockWorld seed 42 recorre `inspect_panel → activate_switch → collect_target → finish` con certificados y agency audit.
- 0 dependencias pip nuevas. 0 Playwright/Selenium.

**Veredicto:** PASS (golden intacto; suite completa 631 passed / 0 failed; el fallo P0 de grounding no se reprodujo en esta corrida y no se reclama como fix de P1).

---

## 2. Contrato

`nexo/core/environment_protocol.py` — métodos reales:

`percepts_for_agent` · `available_actions` · `action_info` · `apply_action` · opcional `sync_from_body` / `action_schemas`.

No se inventó `perceive` / `describe_action`.

---

## 3. ActionSchema

`nexo/core/action_schema.py` — frozen: id, label, action_type, target, affordance, expected_effect, estimated_cost, risk, metadata opaco.

Adapter legacy: `nexo/core/legacy_action_adapter.py` (dueño de `ROOM_ACTION_SCHEMAS`).

---

## 4. MockWorld

`nexo_qa/testing/mock_world.py` — panel/switch, no browser. Bind: `nexo_qa.testing.bind_world`.

---

## 5. Golden

```text
trajectory_hash = 77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c
12 × explore
energy 0.3526710863756767
mean_reward 0.12
421 events, 12 certificates, agency_score 1.0
```

`WorldDemoFacade` sigue **sin** `available_actions` a propósito (P1-RISK-001).

---

## 6. Tests

| Suite | Resultado |
|-------|-----------|
| Full `pytest tests` | **631 passed / 0 failed / 0 skipped** (~65 min) |
| Smoke P0+P1 | 80 passed (~160 s) |
| P0 freeze (referencia) | 604 passed / 1 grounding fail |

Nuevos:

- `tests/test_p1_action_schema.py`
- `tests/test_p1_environment_contract.py`
- `tests/test_p1_two_worlds_one_brain.py`
- `tests/test_p0_nexo_qa_import.py` (antes `tests/nexo_qa/`, movido para no sombrear el paquete)

CI: `.github/workflows/tests.yml` añade el subset P1 **sin** quitar el subset histórico.

---

## 7. Docs

`docs/cognitive_qa/P1_*.md` · `adr/ADR-0002-environment-contract-and-action-schema.md`  
Machine-readable: `artifacts/p1/`

---

## 8. P2

Implementar BrowserWorld sobre el mismo protocolo. Selectores fuera del core. No tocar fórmulas de memoria/TD ni el golden salvo freeze explícito.
