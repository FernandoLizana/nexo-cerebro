# Aprendizaje causal mínimo con soberanía prefrontal en un agente embodied

**Paper nuevo (preprint / workshop)** — distinto de [`paper_completo.md`](paper_completo.md) (ablaciones E1–E3).  
**Sistema:** Nexo (`cerebro`) · **Experimento principal:** E8 Arena Level 2  
**Fecha de resultados Arena:** julio 2026  
**Autores / afiliación:** ver [`AUTHORS.template.md`](AUTHORS.template.md) (TODO)

---

## Resumen

Los agentes basados en LLM suelen mezclar *hablar* y *decidir*. En Nexo, la deliberación prefrontal (`choice_key`) es el único escritor de la acción; el lenguaje es post-hoc. Este trabajo introduce una capa de **aprendizaje causal mínimo**: tras cada interacción real, el agente observa el cambio homeostático corporal y construye un mapa de *affordances* (`objeto + interacción + drive → Δcuerpo`). Esa evidencia solo aporta sesgo Go acotado (±0.08) y un prior de navegación; **nunca** fuerza el motor.

Evaluamos la capa en Arenas reproducibles (perfil compact ~500 neuronas LIF; smoke 10k). Con affordances activas, Nexo vuelve a una fuente novel tras una exposición, generaliza a otra instancia del mismo tipo, discrimina fuente buena vs seca aunque la seca esté más cerca, y aprende hambre/higiene bajo el mismo esquema. Sin affordances, las mismas Arenas agotan el presupuesto sin alivio. Las violaciones de agency reportadas son cero.

**Palabras clave:** affordances; autonomía embodied; deliberación prefrontal; aprendizaje causal; agentes sin LLM-decisor.

---

## 1. Introducción

### 1.1 Problema

En agentes conversacionales, el mismo canal textual suele planificar y actuar. Eso dificulta auditar *quién* eligió mover el cuerpo y hace frágil cualquier claim de “libre albedrío” simulado. Arquitecturas cognitivas clásicas (ACT-R, Leabra) separan módulos, pero rara vez exponen un contrato explícito *evidencia vs selección* en un mundo embodied con homeostasis.

### 1.2 Tesis

Proponemos que un agente embodied puede **aprender consecuencias causales** de sus interacciones y reutilizarlas como evidencia, manteniendo **soberanía absoluta del PFC** sobre `choice_key`:

> Solo `PrefrontalDeliberation.run` escribe la decisión. Affordances, contrafactuales, schemas aprendidos, HUD y LLM no seleccionan acciones.

### 1.3 Preguntas de investigación

| ID | Pregunta |
|----|----------|
| RQ-C1 | ¿Una exposición a un objeto novel basta para guiar el retorno sin GPS hardcodeado? |
| RQ-C2 | ¿La evidencia se transfiere a otra instancia del mismo tipo cuando la original desaparece? |
| RQ-C3 | ¿El agente discrimina dos objetos del mismo tipo (bueno vs fallo) preferiendo el `object_id` exitoso? |
| RQ-C4 | ¿El contrato de agency se mantiene (0 escrituras de `choice_key` fuera del PFC)? |

### 1.4 Contribuciones

1. **AffordanceMap** persistente: observación antes/después corporal, confianza, sesgo ±0.08.
2. **Contrafactual acotado** (±0.06) y schemas `learned_aff_*` que solo amplían el menú PFC.
3. **Arenas E8** (sed, hambre, higiene, transferencia, discriminación, fallo) con flags OFF en batch paper legacy.
4. **Evidencia empírica** compact + smoke 10k; figura `fig9_e8_causal_arena.png`.

El paper hermano [`paper_completo.md`](paper_completo.md) cubre ablaciones de intención, invarianza LLM y sueño (E1–E3 a 10k). Este documento **no** sustituye esas tablas.

---

## 2. Arquitectura (capa causal)

### 2.1 Flujo

```text
drives + percepción
        │
        ▼
PrefrontalDeliberation.run
  concursantes + evidencia acotada
  (affordances ≤±0.08, CF ≤±0.06)
        │
        ▼
choice_key  ← único escritor
        │
        ▼
world.apply_motor → evento
        │
        ▼
AffordanceMap.observe(Δcuerpo)
        │
        ├─ bias Go/No-Go
        ├─ prior de navegación (object_id o tipo)
        └─ (opcional) SchemaLearner.note_affordance_success
```

### 2.2 Contrato de agency

| Módulo | ¿Escribe `choice_key`? |
|--------|-------------------------|
| `AffordanceMap` | No |
| `CounterfactualSimulator` | No |
| `SchemaLearner` (`learned_aff_*`) | No (solo menú) |
| HUD causal / telemetría | No |
| `PrefrontalDeliberation` | **Sí (único)** |
| LLM / Ollama | No (verbalización post-hoc) |

### 2.3 Registro causal

Cada `AffordanceRecord` guarda tipo e id de objeto, interacción, candidate key PFC, drive dominante, media de cambios corporales, ganancia homeostática, éxitos/fallos, error de predicción y confianza. Un alivio insuficiente cuenta como fallo. Las instancias permanecen separadas; la consulta de sesgo elige la evidencia más fuerte por acción, y la navegación prefiere el `object_id` exitoso presente (discriminación) o el nearest del tipo si el id desapareció (transferencia).

### 2.4 Implementación (rutas)

- `brain/affordance_map.py`, `brain/counterfactual_simulator.py`, `brain/learned_schemas.py`
- `brain/agent_loop.py` — priors de caminata
- `brain/deliberation.py` — único writer de `choice_key`
- `docs/NEXO_LEVEL_2.md` — bitácora de versiones V2.1–V2.5

---

## 3. Métodos experimentales (E8)

### 3.1 Perfiles

| Perfil | ~LIF | Uso en este paper |
|--------|------|-------------------|
| `COMPACT_PROFILE` | ~500 | Resultados Arena principales |
| `SCALE_10K_PROFILE` | ~10 290 | Smoke discriminación (1 seed) |
| Demo Flask | 1.4k / demo-lite | HUD; no tablas E8 |

### 3.2 Protocolo Arena

Condiciones `aff_on` / `aff_off` (`enable_affordance_learning`). Headless, `CEREBRO_OLLAMA=0`. Sin GPS gratis a objetos novel (`water_only_novel`, `food_only_novel`, `hygiene_only_novel`). Agency: no se escribe `choice_key` fuera del PFC.

```bash
python -m experiments.run_arena_thirst --seeds 3 --profile compact
python -m experiments.run_arena_extra --seeds 2 --profile compact
python -m experiments.run_arena_level24 --seeds 2 --profile compact
python -m experiments.run_arena_level25 --seeds 2 --profile compact
# smoke 10k
python -m experiments.run_arena_level25 --seeds 1 --profile 10k --out experiments/results/arena_10k
```

### 3.3 Tareas

| Tarea | Descripción |
|-------|-------------|
| Thirst unknown water | Fuente novel; exp.1 cerca → exp.2 lejos |
| Hunger unknown bowl | Cuenco novel análogo |
| Hygiene unknown bath | Bañera novel |
| Transfer A→B | Aprende en A; A se elimina; B del mismo tipo |
| Discrimination | Fuente buena vs seca; spawn cerca de la seca |
| Dry fountain | Fallos + poda en sueño |

---

## 4. Resultados

### 4.1 Resumen (compact, julio 2026)

| Tarea | aff_on | aff_off |
|-------|--------|---------|
| Thirst exp.2 | éxito (~16 ticks típ.) | timeout |
| Hunger exp.2 | éxito (~11 ticks) | timeout |
| Hygiene exp.2 | éxito (~11 ticks) | timeout |
| Transfer A→B | bebe en B (~27 ticks) | falla |
| Discriminación | éxito ~22 ticks; `goal_is_good=True` | timeout; cerca de la seca |
| Fuente seca | fallos, gain≈0 | — |

Artefactos: `experiments/results/arena_*.json`, figura **`experiments/figures/fig9_e8_causal_arena.png`**.

### 4.2 Discriminación (detalle)

Seeds 0–1, compact (`arena_discrimination.json`):

| seed | condición | drank | ticks | goal_good |
|------|-----------|-------|-------|-----------|
| 0 | aff_on | True | 22 | True |
| 0 | aff_off | False | 110 | False |
| 1 | aff_on | True | 22 | True |
| 1 | aff_off | False | 110 | False |

Tras fallar en `fountain-dry` y tener éxito en `fountain-good`, el prior de navegación apunta al bueno aunque la seca esté más cerca del spawn.

### 4.3 Smoke 10k

Una seed (`experiments/results/arena_10k/`): aff_on bebe en **14** ticks con `goal_is_good=True`; aff_off timeout cerca de la seca. Compatible con el claim; no sustituye un barrido multi-seed 10k.

### 4.4 Agency

En todos los brazos reportados, `agency_violations = 0`. El LLM no interviene en el batch (`CEREBRO_OLLAMA=0`).

---

## 5. Discusión

### 5.1 Qué demuestra E8

La evidencia causal observada basta para **guiar retorno, transferir por tipo y discriminar instancias**, sin convertir el mapa de affordances en un planificador. El PFC sigue eligiendo entre concursantes; la capa causal solo inclina Go y el heading.

### 5.2 Limitaciones

- Métricas y Arenas **custom** (no benchmarks externos).
- Resultados principales en **compact**; 10k es smoke.
- Arena usa a menudo `arena_fast_locomotion` para presupuestos de ticks (existe smoke físico).
- Determinismo alto → SD≈0 en varios seeds.
- No afirmamos fidelidad neurobiológica de “affordances” corticales.

### 5.3 Relación con el paper de ablaciones

E1–E3 ([`paper_completo.md`](paper_completo.md)) establecen binding, PFC, hipocampo, afecto, invarianza LLM y sueño. E8 añade **aprendizaje de consecuencias** bajo el mismo contrato de agency.

### 5.4 Trabajo futuro

- Barrido E8 multi-seed a 10k.
- Currícula multi-objeto más ricas.
- PDF CLEI tras rellenar autores.
- Comparación formal con literaturas de affordances / model-based RL acotado.

---

## 6. Reproducibilidad

```bash
pip install -r requirements.txt
python -m experiments.run_arena_level25 --seeds 2 --profile compact
python -m experiments.plot_figures --in experiments/results --fig experiments/figures
python -m pytest tests/test_level23.py tests/test_level24.py tests/test_level25.py tests/test_demo_hud.py -q
```

Flags relevantes (OFF en batch legacy): `CEREBRO_AFFORDANCES`, `CEREBRO_COUNTERFACTUAL`, `CEREBRO_TELEMETRY`, `CEREBRO_LEARNED_SCHEMAS`.

---

## 7. Conclusión

Nexo puede aprender un mapa causal mínimo de interacciones embodied y usarlo como evidencia acotada, preservando la soberanía prefrontal sobre la acción. Las Arenas E8 muestran retorno, transferencia y discriminación con agency intacta. El lenguaje permanece fuera del bucle de decisión.

---

## Referencias (selección)

1. Anderson, J. R., et al. (2004). An integrated theory of the mind. *Psychological Review*.
2. O’Reilly, R. C., & Munakata, Y. (2000). *Computational Explorations in Cognitive Neuroscience*. MIT Press.
3. Gibson, J. J. (1979). *The Ecological Approach to Visual Perception*.
4. Yao, S., et al. (2023). ReAct: Synergizing reasoning and acting in language models.
5. Documentación interna: [`architecture.md`](architecture.md), [`level2_causal_learning.md`](level2_causal_learning.md), [`NEXO_LEVEL_2.md`](../NEXO_LEVEL_2.md).

---

*Manuscrito generado a partir de código y `experiments/results/arena_*.json` (julio 2026). Autores: TODO.*
