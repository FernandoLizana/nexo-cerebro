# P0 — Cognitive capability map

Estado = lo observado en código v90, no una afirmación de fidelidad biológica.  
Acción P0: KEEP / KEEP_AND_WRAP_LATER / SCIENTIFIC_ONLY / LEGACY / UNKNOWN.  
Ningún ADAPT/REFACTOR se ejecutó.

| Capacidad | Implementación actual | Estado | Uso futuro Cognitive QA | Acción |
|-----------|----------------------|--------|-------------------------|--------|
| Percepción | `nexo/core/process_perception.py` `RawSensoryCaptureProcess`, `ThalamicRelayProcess`, `PredictiveHierarchyProcess`; `nexo/perception/*` | OK (modalidades toy) | DOM/accesibilidad limitada | KEEP_AND_WRAP_LATER |
| Atención | `PredictiveAttentionProcess`; `nexo/thalamus/reticular.py`; `brain/attention.py` | OK | búsqueda visual, saliencia UI | KEEP_AND_WRAP_LATER |
| Working memory | `nexo/working_memory/buffer.py` `WorkingMemoryBuffer`; `EnhancedWorkingMemoryProcess` | OK | instrucciones, montos, campos de form | KEEP |
| Memoria episódica | `nexo/memory/hippocampus/store.py` `HippocampalStore`; encoder pri 52 | OK (capacidad 64, eviction) | episodios de sesión web | KEEP |
| Memoria semántica | `brain/memory_systems.py` `TypedMemorySystems` | LEGACY/parcial en nexo | conocimiento de dominio UI | LEGACY |
| Promoción hippo→SQLite | `nexo/core/process_memory_unification.py`; `nexo/demo/memory_unification.py` | OK | persistir errores de usuario | KEEP |
| Memory bridge | `nexo/demo/memory_bridge.py` (advisory) | OK advisory | no fusionar almacenes | KEEP |
| Reward | `MotorExecutionProcess` → `reward.received`; `RoomWorld.apply_action` | OK | éxito/fracaso de goal | KEEP_AND_WRAP_LATER |
| TD learning | `nexo/reinforcement/td_learning.py` `TDRewardSystem`; `TDBiasProcess`/`TDLearningProcess` | OK | sesgo Go, no script | KEEP |
| Deliberación / PFC | `nexo/prefrontal/deliberation.py` `PrefrontalDeliberator`; `ROOM_ACTION_SCHEMAS` | OK acoplado a RoomWorld | decidir acciones web | KEEP_AND_WRAP_LATER |
| Ejecutivo / goals | `nexo/planning/goal_stack.py` `GoalStack` | OK name-locked | goal humano (“comprar dos entradas”) | KEEP_AND_WRAP_LATER |
| BG / selección | `nexo/basal_ganglia/gate.py` `ActionGate` | OK; fallback `rest` | elegir entre acciones DOM | KEEP_AND_WRAP_LATER |
| Afecto | `nexo/core/cognitive_state.py` `AffectiveState`; `nexo/neuromodulation/state.py`; `brain/affect.py` | OK | frustración, abandono | KEEP |
| Frustración | no hay módulo `frustration`; proxies: stress/fatigue/conflict | PARCIAL | Cognitive Friction | KEEP (no inventar) |
| Fatiga | `VirtualBody.fatigue`; drive `rest` | OK | degradación por sesión | KEEP |
| Cuerpo / interocepción | `nexo/body/*`, `nexo/core/process_body.py` | OK | carga cognitiva como homeo | KEEP |
| Curiosidad | `DriveField.drives["curiosity"]`; `brain/curiosity.py` | OK | exploración de UI | KEEP |
| Imaginación | `brain/imagination.py` `ImaginationEngine` | LEGACY | simular “qué pasaría si clic” | LEGACY |
| Predicción / PE | `nexo/perception/prediction_error.py`; `PredictiveHierarchyProcess` | OK | sorpresa de layout | KEEP |
| Metacognición | `nexo/metacognition/monitor.py` `MetacognitiveMonitor` | OK | duda / “no entiendo este form” | KEEP |
| Incertidumbre | PE + metacog confidence; no distribución calibrada | PARCIAL | no overclaim | KEEP |
| Acción / motor | `MotorExecutionProcess`; `UnifiedMotorProcess` (audit) | OK dual-loop risk | click/type/navigate | KEEP_AND_WRAP_LATER |
| Affordances | `brain/affordance_map.py`; nexo `action_info` | PARCIAL | botones/campos como affordances | KEEP_AND_WRAP_LATER |
| Causal certificate | `nexo/behavioral/causal_certificate.py` `build_causal_certificate` | OK v2 post-motor | Cognitive Failure Certificate | KEEP |
| Agency audit | `nexo/behavioral/agency_audit.py`; `nexo/decision_audit.py`; `brain/agency_audit.py` | OK (nexo BG no cubierto por AST) | demostrar no-script | KEEP |
| Event log | `StateStore.event_log` `CognitiveEvent` | OK | traza percibe→actúa | KEEP |
| Tracing | `nexo/telemetry/integrated_trace.py` | PARCIAL (no 10-slot) | observabilidad QA | KEEP |
| Replication | `nexo/behavioral/replication.py` | OK | repetir escenarios QA | SCIENTIFIC_ONLY |
| Permutation / stats / FDR | `nexo/behavioral/permutation.py`, `statistics.py`, `correction.py` | OK | comparar personas | SCIENTIFIC_ONLY |
| Meta-analysis | `nexo/behavioral/meta_analysis.py` | OK | agregados multi-seed | SCIENTIFIC_ONLY |
| Behavioral fingerprint | `nexo/behavioral/fingerprint.py` | OK | firma de persona cognitiva | KEEP |
| Orchestration | `nexo/behavioral/orchestration.py` | OK | no usar para forzar éxito web | SCIENTIFIC_ONLY |
| Task registry | `nexo/behavioral/task_registry.py` `TASK_REGISTRY` | OK | goals humanos ≠ smoke tasks | KEEP_AND_WRAP_LATER |
| World / environment | duck type RoomWorld; factory | OK acoplado | BrowserWorld adapter | KEEP_AND_WRAP_LATER |
| Demo room | `RoomWorld`, Flask `app.py` | OK | no es el producto QA | LEGACY / DEMO |
| Config system | YAML → `IntegratedRuntimeConfig` | OK | flag QA default false | KEEP |
| Agency metrics (proxies) | `nexo/agency_metrics.py` `compute_agency_metrics` | OK; tests propios no hallados | no afirmar libre albedrío | KEEP |
| Symbol cards / hero journey | `brain/archetype_cards.py`, `brain/journey.py` | UNKNOWN | no usar en QA | UNKNOWN |
| LLM / language | `brain/language_cortex.py`; nexo `UtteranceComposer` | verbaliza, no debe decidir | no LLM obligatorio | KEEP |

## Causal certificate — contrato actual (NO modificado)

- **Entrada:** `runtime.state_store.event_log`, tick, `unified_motor_mode`, `sleep_active`.
- **Salida:** dict con `integrated_action`, `action_source`, `legacy_choice_key`, `motor_agreement`, `confidence`, `reward_value`, `advisory_biases`, `agency_contract`, `certificate_valid`, `agency_valid`.
- **Cuándo:** cada tick si `causal_certificate_mode=="integrated"`; proceso priority **50** (post-motor 55).
- **Persistencia:** evento `causal.certificate`; export JSON vía `export_causal_certificate`.
- **Tests:** `tests/test_sprints_71_74_integrated.py`, `tests/test_sprints_75_78_integrated.py`.
- **Limitación:** no incluye percepts, candidatos ni estado posterior; `agency_contract.deliberation_selects_actions` está **hardcodeado True**.

## Agency — contrato actual (NO modificado)

- Runtime: `summarize_agency_audit` + `AgencyAuditProcess` (period 4, pri 49).
- Estático legacy: `nexo/decision_audit.scan_brain_tree` — solo `brain/deliberation.py` puede asignar `choice_key`.
- **Gap:** el BG integrado emite `action.selected` fuera de ese AST.

## Task system (NO modificado)

- Definición: funciones `run_*_task` → `IntegratedTaskResult` (`nexo/behavioral/tasks.py`).
- Registro: `TASK_REGISTRY` (`task_registry.py`).
- Success: métricas externas (`compute_metrics`), no `done` del env. El agente **no** recibe task_id.
- Reward: producido por `apply_action`, leído de `reward.received`.
