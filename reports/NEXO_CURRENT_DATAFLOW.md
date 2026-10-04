# Flujo de datos actual — NEXO

**Actualizado:** 2026-08-04 (rama `feature/nexo-integrated-brain-v1`)

## Legacy (InfantApeBrain)

```mermaid
flowchart TD
    WT[world_tick] --> AL[NeuralAgentLoop.run]
    AL --> INT[interocept]
    INT --> PER[perceive]
    PER --> COG[cognize]
    COG --> DEL[deliberation PrefrontalDeliberation]
    DEL --> ACT[act / motor]
    ACT --> WLD[World2D]
    WLD --> MEM[memory_store / hippocampus modules]
    MEM --> AL
```

**Estado:** disperso en atributos de `InfantApeBrain` (100+ campos).

**Aleatoriedad:** `nexo.random_streams.RandomStreams` inyectado en `mind.py`; residuo en algunos módulos.

## Integrado v1 (Sprint 1)

```mermaid
flowchart TD
    SCH[CognitiveScheduler.step] --> HOM[homeostasis]
    SCH --> SEN[sensory_relay]
    SCH --> INT[interoception]
    SCH --> ATT[attention]
    SCH --> WM[working_memory]
    SCH --> BG[basal_ganglia_selector]
    SCH --> MOT[motor_execution]
    SEN --> RTR[ConnectomeRouter]
    RTR --> STO[StateStore dispatch events]
    BG --> STO
    MOT --> RW[RoomWorld.apply_action]
    RW --> STO
```

**Estado:** `StateStore` con reducers; event log con trazabilidad causal.

**Interfaz pública:** `IntegratedRuntime.run()`; compatible con `nexo.run` CLI.

## Puntos de convergencia planificados

| Legacy | Integrado v1 |
|--------|--------------|
| `brain/deliberation.py` | `nexo/prefrontal/` (Sprint 5) |
| `brain/memory_store.py` | `nexo/memory/hippocampus/` (Sprint 4) |
| `brain/agent_loop.py` | `nexo/core/scheduler.py` |
| `brain/body.py` | `nexo/body/` (Sprint 2) |
