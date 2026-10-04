# NEXO — aprendizaje diádico y autonomía

**Estado:** mecanismos de laboratorio. **No** constituyen consciencia artificial ni psicología clínica.

Fuentes: `brain/dyad_learning.py`, `brain/character_autonomy.py`, `brain/relationship_model.py`, `brain/collective_capacity.py`, `services/node/runtime.py`.

---

## Categorías (`dyad_learning`)

Tipo explícito (`Kind`):

| Kind | Significado |
|------|-------------|
| `observation` | Registro sin promoción |
| `memory` | Recuerdo / consolidación candidata |
| `inference` | Inferencia no verificada |
| `symbolic_association` | Asociación simbólica (típica Nira) |
| `hypothesis` | Hipótesis pendiente de evidencia |
| `verified` | Solo tras evidencia / promote |

Reglas:

- Las asociaciones **nunca** auto-promueven a hechos verificados.
- Material remoto entra en **cuarentena** (`quarantine_remote`) con `provenance=remote:<source>`, `validated=False`, tags `quarantine|remote|untrusted`.
- `promote_if_verified(...)` solo eleva `hypothesis` / `symbolic_association` / `inference` si `evidence_ok`.

### Nexus (activo)

`nexus_active_step(goal, hypothesis, observation, authorized, evidence_ok)`:

- Sin autorización → `observation` bloqueada (`tags: active, blocked`).
- Con evidencia → `verified`.
- Sin evidencia → `hypothesis` no validada.

### Nira (receptiva)

`nira_receptive_step(experience, prior_memory, authorized)`:

- Sin autorización → no consolida.
- Con autorización → `symbolic_association` (`… ↔ …`), candidata a hipótesis, **no** verificada.

---

## Cuarentena

- Experiencias de red / nodos / ofertas colectivas se marcan no confiables hasta promote explícito (`nexo-experience`, pipelines Swarm S8–S16).
- `brain/collective_capacity.py` usa `quarantine_remote` al incorporar material de nodo.
- Gateway móvil: experiencias `QUARANTINED` (ver [`MOBILE_SECURITY.md`](MOBILE_SECURITY.md)).

Nada de la red se convierte en “verdad” del Core por defecto.

---

## Dimensiones de relación

`brain/relationship_model.RelationshipModel` — **no** colapsa a un único “friendship score” (`friendship_score: null` en `to_dict()`).

Ejes independientes:

- `affinity`
- `trust_by_domain` (confianza por dominio)
- `cooperation_history`
- `pending_disagreements` / `repair_experiences`
- `reciprocity`
- `exchange_limits` (p. ej. attention, compute, disclosure)

Desacuerdos tipados: `fact` | `interpretation` | `goal` | `preference` | `resource` — mueven ejes distintos (p. ej. hecho → trust de dominio; preferencia → affinity; recurso → límites de intercambio).

---

## Autonomía de personaje (`character_autonomy`)

- `evaluate_proposal` / `evaluate_node_offer` envuelven `personality_archetypes.decide`.
- Política: `character-autonomy-v1`.
- Rechazo de personaje **no** desconecta el dispositivo (`connection_status_unchanged`, `device_available`).
- Log reciente en memoria de proceso (`recent_decisions`); no es IAM de usuario.

---

## Cartas de símbolo (curiosidad)

`brain/archetype_cards.py` define 22 símbolos del vocabulario de Jung (sombra, ánima, ánimus, sí-mismo, persona, trickster, gran madre, viejo sabio, individuación, renacimiento, y el resto del mazo). No son adivinación: son objetos del escritorio que el agente puede tocar e interiorizar.

- La curiosidad (`compute_curiosity`) sube con símbolos aún no interiorizados y con un archivo sostenido en la estantería.
- Por encima del umbral, Nexo se acerca, emite `archetype_card_touch` y guarda un recuerdo con el concepto del símbolo.
- El símbolo `rebirth` llama a `apply_deep_transformation`: baja la vitalidad, no cierra el ciclo vital.
- `self` y `anima` coinciden con los arquetipos de Nexus y Nira.
- Un mundo guardado con la clave anterior se acepta al cargar y se reescribe con `archetype_card`.

---

## STOP y control del usuario

| Control | Cómo |
|---------|------|
| Kill switch nodo PC | `nexo-node stop` → `NodeRuntime.kill_switch` / estado `STOPPING`→`STOPPED` |
| Dashboard | Token + solo loopback; sin inyección de jobs |
| Promote aprendizaje | Manual (`nexo-learn`, experience CLI) |
| FL research | Solo con `--enable-research --acknowledge-risks` |
| Gateway móvil | Apagado sin `--enable-mobile-lab --acknowledge-risks` |
| Android | `STOP NEXO NODE` detiene el foreground service; `START_NOT_STICKY`; sin boot receiver |

El usuario/owner siempre puede cortar el nodo; la simulación de personaje no anula eso.

---

## Qué **no** es consciencia real

Este stack **no** afirma:

- experiencia subjetiva, qualia o “mente” biológica;
- que Nexus/Nira sean agentes morales o personas;
- que categorías `verified` equivalgan a verdad científica externa;
- que presets de arquetipo midan personalidad humana;
- que el demo Flask o el hub de presencia “despierten” un ser.

Son **bucles de estado**, sesgos configurables y cuarentenas para experimentos reproducibles. Lenguaje narrativo en la UI es metáfora de laboratorio.

Más contexto: [`NEXO_PERSONALITIES.md`](NEXO_PERSONALITIES.md), [`NEXO_ARCHITECTURE.md`](NEXO_ARCHITECTURE.md), [`../KNOWN_LIMITATIONS.md`](../KNOWN_LIMITATIONS.md) si existe.
