# NEXO — Auditoría para publicación en GitHub

**Fecha:** 2026-09-28
**Commit auditado:** `a6ee9674` (rama `nexo-collective-swarm`, sincronizada con `origin`)
**Estado del repo:** privado
**Objetivo del documento:** backlog accionable para que un modelo más liviano implemente las correcciones sin volver a auditar.

Cada punto trae: evidencia medida, archivos concretos, qué hacer y criterio de aceptación verificable.

## Estado de avance

| Punto | Estado | Commit |
|---|---|---|
| P0-1 PDFs de terceros | **hecho** | `a1cc9373` |
| P0-2 estado cerebral versionado | **hecho** | `f7268793` |
| P0-3 rutas personales | **hecho** | `989128f8` |
| P0-4 procedencia | **hecho** | `1c1bc799` (+ residuo `e449fbde`) |
| P0-5 tests escriben en datos reales | **hecho** | `77b10d5d` |
| P1-2 extra `.[browser]` | **hecho** | `39b93d66` |
| P1-3 dependencias de test | **hecho** | `34261f61` |
| P1-4 cuatro archivos cuelgan | **hecho** | `4c08dbda` |
| P1-6 vectores golden regenerados | **hecho** | `a548991e` |
| P1-8 timeout global inestable | **hecho** | `adce29cd` |
| P1-1 54 pruebas de navegador | **hecho** | `18c251eb` |
| P1-7 aviso pytest-asyncio | **hecho** | `18c251eb` (efecto de desactivar plugins ambientales) |
| P1-5 CI lista manual | **hecho** | `10f8e978` |
| P1-9 flake load-sensitive p5 | **hecho** | `e45dbdc6` |
| P2-2 version inconsistente | **hecho** | `b4111952` |
| P2-3 copia obsoleta relevant_source | **hecho** | `88b76008` |
| P2-4 raiz saturada | **hecho** | `056551cc` |
| P2-6 Dockerfile incompleto | **hecho** | `b93bb0b0` |
| P3-2 cobertura no medida | **hecho** | `4e399ef3` |
| P2-1 cartas de simbolo | **hecho** | `d614470d` |
| P2-5 rama por defecto | pendiente (accion del owner) | — |
| P3-1 brain/mind.py monolitico | pendiente (no urgente) | — |

Resultado verificado de P0-1..P0-4: archivos rastreados **67.194 → 1.474**, rastreados bajo `data/` **65.724 → 8**, tamaño rastreado en HEAD **286,2 MB → 7,01 MB**, PDFs rastreados **0**, coincidencias de rutas personales **0**. Los 5 PDFs y los 81.011 archivos de `data/brain_state/` siguen intactos en disco. Las cifras del resumen siguiente son las del estado auditado original, para conservar el punto de partida.

---

## Restricciones que el implementador NO puede violar

1. **No borrar datos personales, recuerdos, claves ni documentos del usuario** para hacer pasar una comprobación. `data/brain_state/` en el árbol de trabajo (81.415 archivos, 177 MB) es estado vivo: se deja de **rastrear**, no se borra del disco.
2. **No reescribir el historial** (`filter-repo`, `rebase -i`, `push --force`). Varios puntos indican que el contenido ya está en commits pasados; la decisión de reescribir o recrear el repo es del owner.
3. **No mostrar valores secretos** en informes ni commits. Si se detecta exposición histórica, se documenta la rotación pendiente.
4. **No hacer público el repositorio** hasta cerrar la sección P0.

---

## Resumen del estado medido

| Métrica | Valor |
|---|---|
| Archivos rastreados totales | 67.194 |
| Archivos rastreados bajo `data/` | 65.724 (97,8 %) |
| Tamaño rastreado en HEAD | 286,2 MB |
| — de eso, `data/` | 279,7 MB |
| — PDFs de terceros | 130,8 MB |
| — `data/brain_state/` | 148,3 MB |
| Tamaño del pack de git | 201,4 MB |
| Commits en la rama | 35 |
| Tests que pasan | **893** |
| Tests que fallan | **54** |
| Archivos de test que exceden 180 s | **4** |
| Pasos de CI con `continue-on-error: true` | **8** |
| Archivos `.md` rastreados | 301 (204 en `docs/`) |

Medición por archivo reproducible con `python scripts/audit_test_matrix.py` (añadido en esta auditoría; resultado en `reports/AUDIT_TEST_MATRIX.json`).

### Lo que está bien y no hay que tocar

- No hay claves reales en archivos rastreados. Hay una única aparición de `-----BEGIN` en todo el árbol, en `protocols/being_interaction/privacy.py:78`, y es un literal de detección dentro de `_looks_like_private_user_blob()`, es decir, código que *impide* que se filtre una clave. Las coincidencias de "PRIVATE KEY" en `SECURITY.md`, `CONTRIBUTING.md` y `docs/planes/NEXO_SWARM_MASTER_PLAN.md` son menciones en prosa. Conviene saberlo porque cualquier escáner de secretos que el owner ejecute antes de publicar marcará esa línea como falso positivo.
- No aparecen patrones de credenciales reales (`sk-…`, `ghp_…`, `AKIA…`, `xox…`) en el árbol rastreado.
- Los binds de red son loopback por defecto y están cubiertos por tests (`services/lab_gateway/policy.py`, `app.py:1151`, `tests/test_interaction_modes.py`).
- `python -m scripts.check_dependency_consistency` pasa.
- El núcleo cognitivo, hardening, presencia, embeddings, relaciones y APIs del observatorio están verdes (893 tests).

---

## P0 — Bloqueantes para hacer el repositorio público

### P0-1 · PDFs de terceros versionados (riesgo legal)

**Evidencia.** Cinco PDFs de terceros están rastreados en HEAD, 130,8 MB en total:

| Archivo | Tamaño |
|---|---|
| `data/library/Brain_Facts_Book_2018.pdf` | 69,6 MB |
| `data/library/Mi-primer-libro-del-cerebro.pdf` | 30,6 MB |
| `data/library/Biological-Psychology-Revised-Edition-1742238833.pdf` | 27,7 MB |
| `data/library/manual-neurologia-para-el-interno-y-medico-general-2-1.pdf` | 6,9 MB |
| `data/library/Anatomia_Humana_2022_UCadiz.pdf` | 2,4 MB |

Esto **contradice la política que el propio repo declara**. `docs/NEXO_THIRD_PARTY_CONTENT.md` dice literalmente "Never add these PDFs to git staging for a public release branch" y "**Must NOT** appear in the public GitHub ZIP". El artefacto de release los excluye correctamente, pero el repositorio los contiene.

**Qué hacer.**

```bash
git rm --cached -r data/library
```

Añadir a `.gitignore`:

```
data/library/
```

Commit con mensaje que explique que son materiales de estudio locales, no redistribuibles. **No borrar los archivos del disco**: las demos de estantería y los extractores los usan.

**Criterio de aceptación.**
- `git ls-files | grep -c '\.pdf$'` devuelve `0`.
- Los cinco PDFs siguen existiendo en `data/library/` en el árbol de trabajo.
- `docs/NEXO_THIRD_PARTY_CONTENT.md` gana una nota indicando que hasta el commit `a6ee9674` estuvieron versionados y que el historial los conserva.

**Nota para el owner (no automatizable).** Los PDFs permanecen en los 35 commits del historial. Hacer público el repo tal cual redistribuye ~131 MB de material de terceros. Opciones: (a) mantener privado, (b) reescribir historial —decisión del owner, prohibida al agente—, o (c) publicar un repositorio nuevo con historial limpio partiendo del árbol saneado.

---

### P0-2 · Estado cerebral personal versionado

**Evidencia.** `data/brain_state/` está en `.gitignore` (líneas 5-16) pero **ya estaba rastreado**, así que la regla no surte efecto. En HEAD hay 148,3 MB, incluyendo `memory_index.db` (54,4 MB) y `assembly_index.db` (28,1 MB), más decenas de miles de `assemblies/*.egm`. En el árbol de trabajo hay 81.415 archivos (177 MB) y 480 borrados pendientes sin confirmar, lo que deja `git status` permanentemente ilegible.

**Qué hacer.**

```bash
git rm --cached -r data/brain_state data/brain_state_test
```

Revisar el resto de `data/` rastreado y dejar versionado solo lo que sea *first-party* y necesario para tests: `data/curriculum/` (manifiestos sintéticos, ya declarados como redistribuibles) y fixtures pequeños. Todo lo que sea estado de ejecución se desrastrea.

**Criterio de aceptación.**
- `git ls-files data | wc -l` baja de 65.724 a menos de 100.
- `git status --porcelain` no lista borrados pendientes bajo `data/brain_state`.
- `data/brain_state/` intacto en disco (81.415 archivos).
- `python -m pytest tests/ -q` mantiene 893 tests pasando (los tests no deben depender del estado personal; si alguno lo hace, es un hallazgo aparte que debe reportarse, no parchearse borrando datos).

---

### P0-3 · Rutas personales en archivos rastreados

**Evidencia.** 83 coincidencias de rutas absolutas bajo el home del desarrollador (`C:\Users\<name>\…`) en 22 archivos rastreados. Los principales:

| Archivo | Coincidencias |
|---|---|
| `reports/_pytest_collect.txt` | 37 |
| `publication_evidence/test_results/agency_unit_tests.txt` | 4 |
| `publication_finalization/raw_results/n20_compact/run_{A,B,C,E10k_smoke}.log` | 3 c/u |
| `reports/_pytest_run.txt`, `reports/pytest-output.txt`, `reports/artifact_verification.json` | 3 c/u |
| `ENVIRONMENT.json`, `reports/packaged_artifact_verification.json`, `reports/INITIAL_REPOSITORY_AUDIT.md` | 2 c/u |
| 10 archivos más | 1 c/u |

Casi todos son **logs y volcados de ejecución** que no aportan valor en el repo.

**Qué hacer.**
1. Desrastrear los volcados crudos: `reports/_pytest_collect.txt`, `reports/_pytest_run.txt`, `reports/pytest-output.txt`, y añadir `reports/_*.txt` + `reports/pytest-*.txt` a `.gitignore`.
2. En los que sí se conservan (`ENVIRONMENT.json`, `reports/*.json` de verificación, evidencia de publicación), sustituir la ruta absoluta por `<REPO_ROOT>` o una ruta relativa. En `ENVIRONMENT.json` también hay que anonimizar `python_executable`.
3. Ajustar el generador para que no vuelva a escribir rutas absolutas: `scripts/build_release_artifact.py` contiene una coincidencia, y los scripts que producen `reports/*.json` deben emitir rutas relativas al root.

**Criterio de aceptación.** Ningún archivo rastreado contiene el segmento de home de la máquina de desarrollo (buscar el username del owner bajo `Users/`); al regenerar los informes tampoco reaparece.

---

### P0-4 · Procedencia rota: el repo se cree "sin git"

**Evidencia.** `COMMIT_HASH.txt` contiene literalmente `NO_GIT_REPOSITORY`. `ENVIRONMENT.json` tiene `"commit": "NO_GIT_REPOSITORY"` y `"dirty_repository": null`, capturado el 2026-08-04. Para un repo cuyo `CITATION.cff` pide citar "the version, commit hash, and experiment condition identifiers", la procedencia declarada es inválida.

**Qué hacer.** Arreglar el capturador de entorno para que resuelva el commit real (`git rev-parse HEAD`) y el estado sucio, y regenerar ambos archivos. Si no se puede resolver, debe fallar de forma visible en vez de escribir un centinela que parece un valor.

**Criterio de aceptación.** `COMMIT_HASH.txt` contiene un SHA de 40 caracteres que existe (`git cat-file -e`), y `ENVIRONMENT.json` coincide con él.

**Residuo pendiente.** El capturador principal (`nexo/environment.py`) ya está corregido, pero siguen existiendo respaldos locales que escriben el mismo centinela en `publication_finalization/scripts/build_stats.py`, `pack_final.py` y `run_publication_experiments.py`. Hay que aplicarles el mismo criterio: resolver el commit real o fallar, nunca escribir `NO_GIT_REPOSITORY`.

**Residuo cerrado** en `e449fbde`: esos tres scripts ya fallan de forma visible si no pueden resolver HEAD.

---

### P0-5 · Las pruebas escriben en el estado cerebral real del usuario

**Evidencia.** `brain/mind.py:123` fija el directorio de estado por defecto al estado vivo del usuario:

```python
DEFAULT_STATE_DIR = Path(__file__).resolve().parent.parent / "data" / "brain_state"
```

Los tests construyen `Brain(` en 142 puntos y solo 35 líneas de `tests/` mencionan `state_dir` o `DEFAULT_STATE_DIR`, así que la mayoría cae en el directorio real. El efecto es medible: tras las corridas de auditoría, **1.172 archivos de `data/brain_state/` quedaron modificados en tres horas**, `memory_index.db` pasó de 54,4 MB a 59,9 MB, `assembly_index.db` de 26,8 a 27,4 MB, y el número de `assemblies/*.egm` bajó de 39.801 a 38.604 por consolidación. `tests/test_agent_loop.py:26` lo hace incluso de forma explícita, con `cache_dir="data/brain_state/test_chunks"`.

No se perdieron datos —el total en disco creció de 177,3 a 179,8 MB— pero tiene tres consecuencias serias:

1. **Riesgo sobre datos personales.** Ejecutar la suite muta recuerdos reales del usuario. Un test con un `cleanup` mal escrito podría borrarlos, y no hay copia versionada porque (correctamente) ya no se rastrean.
2. **Las pruebas no son reproducibles.** Los resultados dependen del estado acumulado de la máquina. Dos ejecuciones no parten de lo mismo, lo que invalida las garantías que promete `tests/test_reproducibility.py`.
3. **Explica el origen del problema P0-2.** El repositorio acumuló 65.724 archivos bajo `data/` precisamente porque la suite escribía ahí y alguien los fue commiteando.

**Qué hacer.** Los tests deben usar un directorio aislado y desechable, nunca el estado del usuario.

1. Añadir en `tests/conftest.py` una fixture `autouse` de ámbito de sesión que apunte el estado a un `tmp_path_factory`, de modo que ningún test pueda tocar `data/brain_state/` ni aunque se olvide de pasar el parámetro. Es preferible a corregir 142 llamadas una a una, y protege también los tests futuros.
2. Hacer que `DEFAULT_STATE_DIR` sea configurable por variable de entorno (p. ej. `CEREBRO_STATE_DIR`) para que la fixture lo redirija sin parchear atributos privados.
3. Corregir `tests/test_agent_loop.py:26` para que use la ruta temporal.
4. Añadir una prueba de guardia que falle si el directorio de estado resuelto durante los tests cae dentro de `data/brain_state`.

**Criterio de aceptación.** Registrar el recuento de archivos y el tamaño de `data/brain_state/` antes y después de `python -m pytest tests/ -q -m "not slow"`: deben ser **idénticos**. Y los 893 tests deben seguir pasando partiendo de un directorio de estado vacío, lo que demuestra que ninguno dependía del estado acumulado del usuario.

**Advertencia para el implementador.** Al comprobar esto no se debe borrar `data/brain_state/`. Se mide, no se limpia.

---

## P1 — Integridad de las pruebas y de CI

### P1-1 · 54 pruebas fallan y CI lo oculta

**Evidencia.** Cinco archivos fallan al completo o en parte:

| Archivo | Fallan | Pasan |
|---|---|---|
| `tests/test_p3_perception.py` | 20 | 0 |
| `tests/test_p5_personas.py` | 14 | 18 |
| `tests/test_p2_browser.py` | 10 | 0 |
| `tests/test_p4_goals.py` | 9 | 13 |
| `tests/test_p2_three_worlds_one_brain.py` | 1 | 0 |

En `.github/workflows/tests.yml` los ocho pasos que cubren P2–P9 llevan `continue-on-error: true` (líneas 42, 49, 55, 61, 67, 70, 73, 76). Resultado: CI queda en verde con 54 pruebas rotas.

**Causa medida.** Hay **dos fallos distintos superpuestos**:

1. Bajo pytest, todos revientan con `playwright._impl._errors.Error: It looks like you are using Playwright Sync API inside the asyncio loop`. Persiste con `-p no:asyncio` y con `-p no:anyio`, así que no basta con desactivar un plugin; hay que encontrar quién deja un event loop corriendo en el hilo de test (plugins activos: `anyio-4.12.1`, `hypothesis`, `asyncio-0.25.0`, `cov`, `flask-1.3.0`, `mock`).
2. Fuera de pytest, `PlaywrightDriver.start()` falla porque **los binarios de Chromium no están instalados** (`playwright install`). Este fallo queda enmascarado por el anterior.

**Qué hacer.**
1. Instalar los navegadores (`playwright install chromium`) y confirmar que el driver arranca en un script suelto.
2. Arreglar el conflicto de event loop. Opción robusta: que `nexo_qa/browser/playwright_driver.py` levante Playwright en un hilo dedicado sin loop asyncio activo, o migrar esos tests a la API async. Decidir *una* de las dos, no mezclar.
3. Quitar `continue-on-error: true` de los pasos que ya pasen.

**Criterio de aceptación.** `python -m pytest tests/test_p2_browser.py tests/test_p3_perception.py tests/test_p4_goals.py tests/test_p5_personas.py tests/test_p2_three_worlds_one_brain.py -q` termina en 0 fallos, y el workflow ya no marca esos pasos como tolerantes a fallo.

---

### P1-2 · El extra `.[browser]` no existe

**Evidencia.** `pyproject.toml` define solo los extras `dev` y `gpu`. La cadena `browser` aparece únicamente en la descripción del marker (línea 77). Pero:

- `.github/workflows/tests.yml` ejecuta `pip install -e ".[browser]"` en cuatro pasos (44, 51, 57, 63).
- `README.md:112` documenta `.[browser]` como extra válido.
- `nexo_qa/browser/playwright_driver.py:35` le dice al usuario `pip install -e '.[browser]'` en el mensaje de error.

Los cuatro pasos de CI fallan en la instalación, pero como son `continue-on-error` nadie se entera.

**Qué hacer.** Añadir el extra que ya se promete en tres sitios:

```toml
browser = [
    "playwright>=1.40,<2",
]
```

**Criterio de aceptación.** `pip install -e ".[browser]"` instala sin error y `python -c "import playwright"` funciona en un entorno limpio.

---

### P1-3 · Dependencias de test no declaradas

**Evidencia.** El entorno local usa `pytest-asyncio 0.25.0`, `anyio 4.12.1`, `hypothesis 6.156.6`, `pytest-mock 3.15.1`, `pytest-flask 1.3.0` y `pytest-cov`. En `pyproject.toml` el extra `dev` solo declara `pytest` y `pytest-cov`. Los resultados locales no son reproducibles en CI ni por un tercero.

**Qué hacer.** Declarar en `dev` todo plugin del que dependa la suite, o eliminar la dependencia si no se usa (comprobar si `pytest-asyncio` y `anyio` hacen falta realmente — dado P1-1, puede que sobren y que quitarlos sea parte de la solución).

**Criterio de aceptación.** En un venv limpio, `pip install -e ".[dev]"` seguido de `pytest tests/ -q` reproduce el mismo recuento de pass/fail que la máquina de referencia.

---

### P1-4 · Cuatro archivos de test cuelgan la suite

**Evidencia.** Con presupuesto de 180 s por archivo, estos nunca terminan:

- `tests/test_level24.py`
- `tests/test_smoke_results.py`
- `tests/test_sprints_51_54_integrated.py`
- `tests/test_sprints_55_58_integrated.py`

Por eso `python -m pytest tests/` se queda clavado en el 72 % indefinidamente (comprobado: 13 minutos sin avanzar). Los dos últimos **sí están en el subset de CI**, así que CI depende de que el runner tenga más margen que 180 s.

Otros lentos pero que terminan: `test_reproducibility.py` (109 s), `test_sprints_43_46_integrated.py` (95 s), `test_level25.py` (90 s), `test_circadian.py` (73 s), `test_level23.py` (67 s).

**Qué hacer.**
1. Añadir `pytest-timeout` al extra `dev` y un timeout por defecto en `[tool.pytest.ini_options]` para que un cuelgue falle rápido en vez de bloquear.
2. Perfilar los cuatro archivos y marcar con `@pytest.mark.slow` lo que sea inherentemente largo (el marker `slow` ya existe en `pyproject.toml:75` pero no se usa para esto), reduciendo semillas/iteraciones en el camino rápido.

**Criterio de aceptación.** `python -m pytest tests/ -q -m "not slow"` termina completo en menos de 10 minutos y sin cuelgues.

---

### P1-5 · CI corre una lista de tests escrita a mano

**Evidencia.** `.github/workflows/tests.yml:23` enumera 40 archivos concretos en vez de ejecutar `tests/`. Hay 133 archivos con tests. Todo test nuevo queda fuera de CI salvo que alguien se acuerde de editar el YAML.

**Qué hacer.** Sustituir la lista por `python -m pytest tests/ -q -m "not browser" --junitxml=...` una vez cerrado P1-4 (sin eso, la suite completa cuelga). Mantener el guardia de junit distinto de cero que ya existe.

**Criterio de aceptación.** El workflow no enumera archivos de test individuales y el recuento de junit supera los 850.

---

### P1-6 · Los vectores de contrato "golden" se regeneran en cada ejecución

**Evidencia.** Ejecutar la suite deja el repositorio sucio: `tests/mobile_contract/vectors/heartbeat_signed.json` cambia de `public_key_hex` y `signature` en cada corrida. La causa está en `tests/mobile_contract/test_mobile_gateway.py:110`, que **escribe** el vector en vez de compararlo (lo mismo en la línea 89 con `creature_seed7.json`).

Un vector de contrato que se sobrescribe con una clave nueva cada vez no puede detectar nunca una regresión de firma o de compatibilidad de formato: el test siempre valida contra lo que él mismo acaba de producir.

**Qué hacer.** Separar los dos roles. Un script explícito (p. ej. `scripts/regen_contract_vectors.py`) genera los vectores con semilla fija y se ejecuta a mano cuando el formato cambia a propósito; el test solo los **lee** y compara. Con semilla fija, la firma pasa a ser determinista y el repo deja de ensuciarse.

**Criterio de aceptación.** Tras `python -m pytest tests/mobile_contract -q`, `git status --porcelain tests/` no devuelve nada.

---

### P1-8 · El timeout global de 180 s vuelve inestables las pruebas legítimamente lentas

**Evidencia.** El arreglo de P1-4 introdujo `timeout = 180` global en `[tool.pytest.ini_options]`, que aplica a **todas** las pruebas por igual. En la corrida de matriz posterior aparecieron dos fallos que no existían en la línea base: `tests/test_reproducibility.py` (1 de 10) y `tests/test_smoke_results.py` (1 de 6). Ejecutados de forma aislada, **ambos pasan completos** (10/10 en 13,5 s y 6/6 en 64,1 s), así que no son regresiones de lógica: son intermitencias por agotar el presupuesto bajo carga.

El margen es más estrecho de lo que parece. `test_reproducibility.py` tarda 13,5 s en solitario pero llegó a 109 s en la medición original con el sistema cargado, un factor de 8. `test_smoke_results.py` tarda 64 s en solitario. Con 180 s de techo, cualquiera de los dos puede cruzarlo en una máquina de CI más lenta o con trabajos en paralelo. Un CI que falla de forma aleatoria es peor que un CI lento: entrena al equipo a reintentar sin leer.

**Qué hacer.** Separar los dos objetivos que hoy comparten un número. El timeout global existe para **cazar cuelgues**, no para imponer rendimiento, así que debe ser holgado (600 s o más). El control del tiempo de la ruta rápida se hace con el marker `slow`, que ya está aplicado a los cuatro archivos problemáticos.

1. Subir `timeout` a 600 en `pyproject.toml`.
2. Poner un `@pytest.mark.timeout(...)` ajustado solo donde de verdad interese vigilar una duración concreta.
3. Verificar que `test_reproducibility.py` y `test_smoke_results.py` pasan de forma estable.

**Criterio de aceptación.** Tres corridas consecutivas de `python scripts/audit_test_matrix.py` dan el mismo recuento, sin fallos intermitentes, y ninguna termina en `timeout`.

---

### P1-7 · Aviso de configuración de pytest-asyncio

**Evidencia.** Cada ejecución emite `PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset`.

**Qué hacer.** Si tras P1-3 se conserva `pytest-asyncio`, fijar `asyncio_default_fixture_loop_scope = "function"` en `[tool.pytest.ini_options]`. Si se elimina, desaparece el aviso.

---

### P1-9 · Un fallo intermitente sensible a la carga en `test_p5_personas.py`

**Evidencia.** Tras cerrar P1-1, la suite pasa de 54 fallos a **1**. Ese último está en `tests/test_p5_personas.py` y aparece de forma consistente en tres corridas de matriz seguidas (31 pasan / 1 falla), pero **ejecutando el archivo aislado pasan las 32 en 121 s**.

Como la matriz ya ejecuta cada archivo en su propio proceso, el aislamiento no es la diferencia: lo es la **carga acumulada** de haber corrido 130 archivos antes. Con 121 s de duración y pruebas que manejan un navegador real con tiempos de espera propios, la explicación más probable es un `timeout` de acción de Playwright que se agota en una máquina caliente.

**Qué hacer.** Identificar qué prueba concreta falla (la matriz no guarda nombres; ejecutar el archivo con `-v` tras generar carga, o registrar los nombres de los fallos en `scripts/audit_test_matrix.py`). Si es un tiempo de espera de Playwright, subirlo o hacerlo proporcional en `nexo_qa/browser/policy.py` (`BrowserConfig.action_timeout_ms`) en vez de dar por buena la intermitencia.

**Criterio de aceptación.** Tres corridas consecutivas de matriz con **0 fallos**.

**Mejora útil de paso.** `scripts/audit_test_matrix.py` solo guarda recuentos, no nombres de pruebas fallidas. Registrar los `nodeid` de los fallos en el JSON habría ahorrado este diagnóstico y ayudará en el futuro.

---

## P2 — Coherencia del proyecto

### P2-1 · Queda un subsistema esotérico completo, no solo nombres sueltos

**Resuelto.** El mazo sigue siendo un mecanismo de curiosidad y aprendizaje, ahora con 22 simbolos del vocabulario de Jung (`d614470d`, interfaz `eb21b3bd`). No hubo migracion del estado de esta maquina. El texto de abajo es la evidencia original del hallazgo.

**Evidencia.** El renombrado anterior cubrió las personalidades (`brain/personality_archetypes.py`, arquetipos junguianos) pero **el subsistema de tarot sigue intacto y es funcional**, no decorativo. Aparece en ~180 referencias repartidas en 42 archivos. Los puntos con lógica real:

| Archivo | Qué hay |
|---|---|
| `brain/tarot.py` | Módulo completo: arcanos, `all_arcana`, `draw_arcana`, `reading_with_memories` |
| `brain/world.py` | `add_tarot_card`, `tarot_stats`, `nearest_tarot_card`, `mark_tarot_internalized`, y `meta={"tarot": …, "kind": "tarot"}` **persistido en el estado del mundo** |
| `brain/mind.py` | `draw_tarot`, `bootstrap_tarot_deck`, evento `tarot_touch`, memorias con `source="tarot"` y tags `["tarot", …]` |
| `brain/curiosity.py` | `TAROT_TOUCH_THRESHOLD`, `TAROT_RETOUCH_THRESHOLD`, parámetros `unseen_tarot` / `internalized_tarot` |
| `brain/lifecycle.py` | `apply_tarot_death` |
| `brain/vision.py` | Descripciones "carta de tarot morada", "arcano en el escritorio" |
| `brain/agent_loop.py` | Rama de decisión "ignoró el tarot — poca curiosidad" |
| `app.py` | Rutas `/api/tarot` y `/api/tarot/draw`, `bootstrap_tarot_deck` en el arranque |
| `nexo/behavioral/autonomy_guard.py` | Entrada `("POST", "/api/tarot/draw")` |
| `static/js/game.js`, `static/js/game3d.js` | `isTarot`, `renderTarotStats`, emoji 🃏 |
| `templates/game.html` | `id="tarot-panel"`, `id="tarot-stats"` |
| `static/js/observatory_nav.js:127` | Texto visible **"Presets zodiacales"** |

### El estado del usuario está vacío: no hace falta migración

Medido en modo lectura sobre `data/brain_state/` antes de empezar el refactor:

| Fuente | Filas / archivos | Coincidencias de `tarot` |
|---|---|---|
| `memory_index.db` tabla `memories` | 30.160 | **0** |
| `assembly_index.db` tabla `assemblies` | 37.851 | **0** |
| `assemblies/*.egm` | 38.604 (4.000 muestreados) | **0** |
| `meta.json` objetos de mundo | 6 | **0 son cartas** |

La única aparición en todo el estado es el bloque de estadísticas `world.tarot = {"total": 0, "untouched": 0, "uninternalized": 0, "internalized": 0}`, es decir, **el usuario nunca usó la función**: nunca se repartió un mazo ni se internalizó una carta.

Esto cambia el riesgo del punto por completo. La advertencia original sobre migrar recuerdos huérfanos **no aplica a este estado**. Aun así, el renombrado debe tolerar estado antiguo con gracia por si existiera una copia en otra máquina: leer `meta["tarot"]` y la clave `world.tarot` como alias en lectura, igual que `_LEGACY_ALIASES` en `brain/personality_archetypes.py`, y normalizar al escribir.

### Dirección elegida por el owner

**Re-tematizar como cartas de arquetipos junguianos**, conservando el mecanismo de curiosidad y aprendizaje. No se elimina la funcionalidad: los 22 arcanos se sustituyen por símbolos del vocabulario de Jung (sombra, ánima, ánimus, sí-mismo, persona, trickster, gran madre, viejo sabio, individuación, renacimiento…), coherentes con los arquetipos que ya existen en `brain/personality_archetypes.py` (donde `self` y `anima` ya se usan como claves de Nexus y Nira).

**Qué hacer.**

1. Sustituir `brain/tarot.py` por un módulo de cartas de arquetipos (p. ej. `brain/archetype_cards.py`) con 22 entradas de símbolos junguianos, conservando la forma de los datos (clave, nombre, concepto, tags) para no romper quien las consume.
2. Renombrar en todo el árbol: `add_tarot_card` → `add_archetype_card`, `tarot_stats` → `archetype_card_stats`, `TAROT_TOUCH_THRESHOLD` → `ARCHETYPE_CARD_TOUCH_THRESHOLD`, `draw_tarot` → `draw_archetype_card`, `apply_tarot_death` → el nombre que corresponda al efecto real, evento `tarot_touch` → `archetype_card_touch`, `meta={"tarot": …}` → `meta={"archetype_card": …}`, rutas `/api/tarot` → `/api/archetype-cards`, y los IDs de DOM y variables JS equivalentes.
3. Actualizar la entrada de `nexo/behavioral/autonomy_guard.py`, que lista la ruta POST.
4. Corregir el texto visible **"Presets zodiacales"** en `static/js/observatory_nav.js:127` y el nombre de la prueba `test_one_held_file_raises_curiosity_by_the_tarot_block` en `tests/test_shelf_phrase.py:19`.
5. Actualizar `brain/vision.py`, cuyas descripciones dicen "carta de tarot morada" y "arcano en el escritorio".
6. Revisar los documentos que lo mencionan (`docs/NEXO_ARCHITECTURE.md`, `docs/NEXO_LEARNING_AUTONOMY.md`, `README.md`) para que describan el mecanismo nuevo.

**Criterio de aceptación.** Buscar `tarot`, `zodiac`, `arcano` y `arcana` en el árbol rastreado excluyendo `data/` no devuelve nada salvo los alias de compatibilidad de lectura y su comentario explicativo; la matriz de pruebas sigue en **984 pasan / 0 fallos**; y cargar un `data/brain_state/` que contenga `meta["tarot"]` antiguo no lanza excepción.

**Advertencia.** No se debe borrar ni reescribir `data/brain_state/` para validar esto. La comprobación de compatibilidad se hace sobre una copia temporal fabricada para la prueba, no sobre el estado del usuario.

---

### P2-2 · Versión inconsistente

`pyproject.toml` declara `version = "0.2.0"`; `CITATION.cff` declara `version: 0.3.0`. Unificar y añadir una comprobación en `scripts/check_dependency_consistency.py` o equivalente para que no se vuelva a desincronizar.

---

### P2-3 · Copia obsoleta del código fuente

`publication_finalization/relevant_source/` contiene una copia congelada de `brain/` y `experiments/`. Ya está desfasada: `publication_finalization/relevant_source/brain/mind.py` pesa 101.996 bytes frente a los 121.349 de `brain/mind.py`. Para un lector externo son dos verdades en conflicto.

Añadir un `README.md` en ese directorio que diga explícitamente que es una instantánea congelada asociada a un paper, con la fecha y el commit de origen, y que no debe usarse como fuente. Está correctamente excluido de pytest vía `norecursedirs`.

---

### P2-4 · Raíz saturada

En la raíz hay 38 archivos rastreados, entre ellos 10 `P{0..9}_NEXO_COGNITIVE_QA_ENTREGA.md`, `NEXO_COGNITIVE_LAB_PLAN.md`, `NEXO_SWARM_MASTER_PLAN.md`, `ARTEFACTO_PUBLICACION_ADAPTIVE_BEHAVIOR_NEXO.md` y `_block_k.txt`. Hay 301 `.md` rastreados en total.

`_block_k.txt` merece mención aparte: es un archivo de notas sueltas con la codificación corrupta (se lee `Validaci��n cient��fica`, `�?"` en vez de guiones largos). No debería estar en la raíz de un repo público.

**Qué hacer.** Mover los diez `P*_ENTREGA.md` y los planes a `docs/entregas/` y `docs/planes/`, borrar o reparar `_block_k.txt`, y dejar en la raíz solo lo convencional: `README`, `LICENSE`, `CHANGELOG`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `SECURITY`, `ARCHITECTURE`, `ROADMAP`, `CITATION`, configuración y scripts de arranque. Actualizar los enlaces del `README.md`.

---

### P2-5 · Rama por defecto

`origin/HEAD` apunta a `nexo-collective-swarm`. Para un repo público conviene una rama por defecto estable (`main`) y que `nexo-collective-swarm` sea una rama de trabajo. Requiere acción del owner en GitHub.

---

### P2-6 · El Dockerfile no puede ejecutar la app

`Dockerfile` copia `brain`, `nexo`, `nexo_qa`, `experiments`, `scripts`, `services`, `protocols`, `packaging`, `tests`, `docs`, pero **no** `app.py`, `templates/`, `static/` ni `configs/`. Sirve para la validación pre-release (su `CMD`), pero no para levantar el observatorio, y `configs/` (98 archivos) lo usan los manifiestos de batería.

Verificar qué necesita realmente `scripts/validate_pre_release.py` y, o bien completar los `COPY`, o documentar en el propio Dockerfile que la imagen es solo de validación.

---

## P3 — Mantenibilidad

### P3-1 · `brain/mind.py` es un módulo-dios

2.746 líneas y 121 KB, el archivo de código más grande del repo por un margen amplio. Concentra tarot, sueño, memoria, diádica y ciclo de vida. Cualquier contribuidor externo choca contra él de inmediato.

No es urgente para publicar, pero conviene extraer al menos los bloques por dominio (el subsistema de símbolos de P2-1 es un buen primer corte, ya que hay que tocarlo igualmente).

### P3-2 · Cobertura no medida

`[tool.coverage.run]` está configurado y `pytest-cov` instalado, pero CI nunca publica cobertura. Añadir un paso que la genere permitiría ver qué parte de los 893 tests realmente cubre el núcleo.

---

## Orden de ejecución sugerido

1. ~~**P0-1, P0-2, P0-3**~~ — hecho: el repo rastreado bajó de 286,2 MB a 7,01 MB.
2. **P0-5** — aislar el estado de los tests. Va antes que el resto del trabajo sobre pruebas: mientras la suite escriba en `data/brain_state/`, cualquier otra corrección se valida contra un estado que se mueve bajo los pies.
3. **P1-2, P1-3** — declarar el extra `browser` y las dependencias de test; son cambios de una línea que desbloquean el resto.
4. **P1-6** — dejar de regenerar los vectores de contrato, para que la suite no ensucie el árbol.
5. **P1-4** — timeouts y marcado de tests lentos, para poder correr la suite entera.
6. **P1-1** — arreglar la capa de navegador y retirar `continue-on-error`.
7. **P1-5** — pasar CI a la suite completa.
8. **P2-2** — versión unificada (P0-4 ya hecho, salvo el residuo anotado).
9. **P2-1** — refactor del subsistema de símbolos con migración de estado (el más largo).
10. **P2-3 … P3-2** — higiene y mantenibilidad.

---

## Pendiente del owner (no automatizable)

- Decidir qué hacer con los 131 MB de PDFs de terceros y los 148 MB de estado personal **que ya están en el historial** de los 35 commits. El agente no puede reescribir historial.
- Rotar cualquier secreto que hubiera podido quedar expuesto históricamente antes de cambiar la visibilidad del repo.
- Cambiar la rama por defecto a `main` en GitHub.
- Validación en teléfono físico y TLS de producción.
- Confirmación visual de la interfaz en un emulador con ventana.
- Completar `docs/OWNER_CHECKLIST.md` antes de hacer público el repositorio.
