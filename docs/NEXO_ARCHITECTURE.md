# NEXO — arquitectura (GitHub)

**Estado:** laboratorio experimental. **No** es un producto multi-tenant listo para producción.

Este documento enlaza las capas que un visitante de GitHub necesita ver juntas: demo Flask, presence hub, lab gateway, brain, nodo Android y contratos. El detalle del Swarm S0–S17 sigue en [`NEXO_SWARM_ARCHITECTURE.md`](NEXO_SWARM_ARCHITECTURE.md) y [`ARCHITECTURE.md`](../ARCHITECTURE.md).

---

## Vista rápida

```text
┌─ LEGACY / DIDÁCTICO ─────────────────────────────────────┐
│  app.py (Flask) · brain/ · data/brain_state/             │
│  UI neuro-inspirada en loopback — no es el control plane │
└──────────────────────────────────────────────────────────┘

┌─ PRESENCE HUB (local visual) ────────────────────────────┐
│  services/presence/ · puerto 8770 · token local           │
│  Estantería / pares / LIF — mutaciones con token          │
└──────────────────────────────────────────────────────────┘

┌─ COLLECTIVE SWARM ───────────────────────────────────────┐
│  services/node · being · memory · lab · learning · …     │
│  nexo-dashboard (solo loopback) · nexo-lab               │
└──────────────────────────────────────────────────────────┘

┌─ MOBILE LAB (opt-in) ────────────────────────────────────┐
│  protocols/mobile · services/lab_gateway · apps/android  │
│  Apagado por defecto; requiere flags de riesgo           │
└──────────────────────────────────────────────────────────┘

┌─ CORE CIENTÍFICO (protegido) ────────────────────────────┐
│  nexo/ + nexo_qa/ — MessageBus in-process                │
│  Swarm no reescribe el Core                             │
└──────────────────────────────────────────────────────────┘
```

---

## Componentes

| Pieza | Ruta | Rol |
|-------|------|-----|
| Flask demo | `app.py`, `static/`, `templates/` | Cerebro didáctico + APIs `/api/*` en loopback |
| Brain | `brain/` | Mente, aprendizaje diádico, arquetipos, relaciones, autonomía de personaje |
| Presence hub | `services/presence/` | Hub visual local (pares, estantería, capacidad colectiva) |
| Lab gateway | `services/lab_gateway/` | TLS + emparejamiento móvil; verificación de clave registrada |
| Swarm node | `services/node/` | Nodo voluntario PC: jobs allowlisted, kill switch |
| Being / memory | `services/being/`, `services/memory/local/` | Persistencia por Being; path containment |
| Core | `nexo/`, `nexo_qa/` | Runtime determinista + QA cognitivo P0–P9 |
| Android node | `apps/android-node/` | Nodo Kotlin Tier 0 (Creature/LIF enteros) |
| Contratos | `protocols/mobile/`, `protocols/events/`, `protocols/being_interaction/`, `protocols/lif/` | Envelopes y codecs fail-closed |

---

## Ciclos Nexus / Nira

| Personaje | Arquetipo | Aprendizaje | Ciclo (resumen) |
|-----------|-----------|-------------|-----------------|
| **Nexus** (aliases `nexus`, `nexo`) | Sí-mismo (`self`) | Activo | goal → hipótesis → acción autorizada → observación → evaluación → aprendizaje |
| **Nira** | Ánima (`anima`) | Receptivo | experiencia autorizada → observación → asociación → consolidación → hipótesis → verificación opcional |

Implementación: `brain/personality_archetypes.py` (perfiles), `brain/dyad_learning.py` (pasos), `brain/character_autonomy.py` (decisión de personaje). Detalle: [`NEXO_LEARNING_AUTONOMY.md`](NEXO_LEARNING_AUTONOMY.md), [`NEXO_PERSONALITIES.md`](NEXO_PERSONALITIES.md).

---

## Tres planos que no se deben mezclar

| Plano | Qué es | Qué **no** es |
|-------|--------|----------------|
| **Autonomía simulada** | `decide()` / `evaluate_proposal()` sesgan accept/reject/… | Conciencia real ni voluntad |
| **Autorización de usuario** | Consentimiento, flags, promote manual, STOP | “El personaje decidió por ti” |
| **Disponibilidad de dispositivo** | Nodo encendido, red, recursos, kill switch | Rechazo de personaje ≠ desconexión |

Un `reject` de personaje deja `connection_status_unchanged: true` y no implica cortar el nodo.

---

## Rutas soportadas vs legacy

### Soportadas (lab / Swarm / móvil)

- CLIs Swarm: `nexo-node`, `nexo-lab`, `nexo-dashboard`, `nexo-experience`, `nexo-learn`, …
- Gateway móvil: `nexo-lab-gateway` con `--enable-mobile-lab --acknowledge-risks`
- Contratos `mobile-v1` + tests en `tests/mobile_contract/`
- Core: `python -m nexo.run`, baterías en `experiments/`
- Presence hub local (loopback + token) para demos visuales de pares

### Legacy / didácticas (mantener, no priorizar en GitHub)

- `python app.py` → Flask en `127.0.0.1:5000` (demo neuro-UI)
- Persistencia densa en `data/brain_state/` (no commitear; ver `.gitignore`)
- Rutas de anatomía / GPU / Ollama opcionales en el demo Flask
- Cartas de símbolo (`brain/archetype_cards.py`, `GET /api/archetype-cards`): 22 figuras del vocabulario de Jung que el agente puede tocar e interiorizar por curiosidad. No son adivinación. El estado viejo que guardaba la carta bajo la clave anterior se lee y se normaliza al guardar.
- Packaging SaaS / portal cliente: **eliminado** y gitignored

### Fuera de alcance

- Escanear LAN, instalación silenciosa, shell remoto, FL por defecto
- Multi-tenant IAM, “AGI product”, claims de consciencia biológica

---

## Contratos y fail-closed

- **Móvil:** envelope firmado Ed25519; nodos *approved* deben usar la **clave registrada** (`services/lab_gateway/verify.py`). Una clave solo en el mensaje no prueba identidad.
- **Jobs:** allowlist; `EXECUTE_SHELL` y jobs hostiles se rechazan.
- **Experiencias remotas:** cuarentena hasta promote explícito.
- **Browser QA:** `BrowserPolicy` solo loopback por defecto (`nexo_qa/browser/policy.py`).

---

## Documentación relacionada

| Tema | Doc |
|------|-----|
| Personalidades | [`NEXO_PERSONALITIES.md`](NEXO_PERSONALITIES.md) |
| Aprendizaje / autonomía | [`NEXO_LEARNING_AUTONOMY.md`](NEXO_LEARNING_AUTONOMY.md) |
| Seguridad | [`NEXO_SECURITY.md`](NEXO_SECURITY.md) |
| Instalación | [`NEXO_INSTALL.md`](NEXO_INSTALL.md) |
| Móvil | [`MOBILE_NODE_ARCHITECTURE.md`](MOBILE_NODE_ARCHITECTURE.md), [`MOBILE_PAIRING.md`](MOBILE_PAIRING.md) |
| Swarm | [`NEXO_SWARM_ARCHITECTURE.md`](NEXO_SWARM_ARCHITECTURE.md) |
| CI / Docker | [`DOCKER_VALIDATION.md`](DOCKER_VALIDATION.md), `.github/workflows/tests.yml` |
