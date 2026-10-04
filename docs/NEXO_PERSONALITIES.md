# NEXO — arquetipos de personalidad (inspiración jungiana)

**Advertencia:** presets de **diseño** que sesgan decisiones simuladas. **No** son tipología clínica, ni psicología validada, ni astrología.

Fuente: `brain/personality_archetypes.py` · autonomía: `brain/character_autonomy.py`.

---

## Nexus y Nira

| Nombre | Aliases | Arquetipo | Rol (metáfora de laboratorio) | Aprendizaje |
|--------|---------|-----------|-------------------------------|-------------|
| **Nexus** | `nexus`, `nexo` | **Self** (Sí-mismo) | Consciencia funcional activa | Ciclo activo |
| **Nira** | `nira` | **Ánima** receptiva | Subconsciente funcional receptivo | Ciclo receptivo |

Complementariedad (intercambio y equilibrio dinámico), no jerarquía. Nira tiene iniciativa; Nexus también puede observar.

Defaults de sesgo en `decide()` si no se pasa arquetipo:

- Nexus → `outlaw` (apertura / innovación)
- Nira → `mystic` (asociación / contexto)

---

## Los 12 presets

| Clave | Nombre | Foco jungiano (metáfora) | Tendencia | Tensión a regular |
|-------|--------|--------------------------|-----------|-------------------|
| `hero` | El Héroe | Self / impulso consciente | Iniciativa y estructura | Impulsividad |
| `innocent` | El Inocente | Child | Continuidad y estabilidad | Rigidez |
| `lover` | El Amante | Anima/Animus relacional | Comparar alternativas | Dispersión |
| `caregiver` | El Cuidador | Great Mother | Proteger vínculos | Sobreprotección |
| `creator` | El Creador | Persona expresiva | Expresión y coraje | Reconocimiento excesivo |
| `sage` | El Sabio | Senex | Análisis y verificación | Parálisis por análisis |
| `everyman` | El Ciudadano | Persona social | Reciprocidad y mediación | Indecisión |
| `magician` | El Mago | Trickster | Transformar patrones | Descartar pronto |
| `explorer` | El Explorador | Puer | Explorar e integrar | Generalizar sin evidencia |
| `ruler` | El Soberano | Self estructurante | Recursos e incentivos | Apego al control |
| `outlaw` | El Rebelde | Shadow / ruptura | Innovación colectiva | Idealismo |
| `mystic` | El Introspectivo | Ánima receptiva | Asociación e imaginación | Confundir interpretación con hechos |

Los rasgos (`curiosity`, `caution`, `impulsivity`, …) sesgan **decisiones** (aceptar / rechazar / negociar / posponer / pedir info / descansar), no solo el vocabulario.

---

## Aliases legacy

Claves antiguas (nombres de signos) se resuelven a arquetipos para no romper estados guardados. Ver `_LEGACY_ALIASES` en el módulo.

---

## API

- `get_preset(name)`, `all_presets()`, `decide(archetype=…, proposal=…, trust=…, seed=…)`
- `policy_version`: `jung-archetype-autonomy-v1`
- Rechazo del personaje **no** implica desconexión del dispositivo (`connection_status_unchanged`)

Cartas simbólicas en la casa 3D (si existen en el mundo) se tratan como **símbolos de arquetipo / memoria**, no como adivinación.
