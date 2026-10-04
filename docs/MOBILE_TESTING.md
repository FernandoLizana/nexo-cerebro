# Tests

Python (corre en este PC):

```bash
python -m pytest tests/mobile_contract/test_mobile_gateway.py tests/test_swarm_core_fortress.py -q
```

Cubren: bind no público, jobs prohibidos, motor entero estable (seed 7), firma y tamper, pairing de un solo uso, job desconocido, replay, experiencia en cuarentena.

Kotlin:

- `app/src/test/.../CreatureTier0Test.kt` — mismo vector seed 7 (`FLEE`, energy 630).
- `app/src/androidTest/.../KillSwitchInstrumentedTest.kt` — la sesión no queda activa tras stop.

Vectores: `tests/mobile_contract/vectors/`.

No hay emulador en este SDK vacío. Los tests instrumentados quedan en el árbol para cuando exista un AVD.

Teléfono físico: ver [`NEXO_INSTALL.md`](NEXO_INSTALL.md) § Teléfono físico y [`MOBILE_PAIRING.md`](MOBILE_PAIRING.md). Smoke del gateway (loopback):

```bash
python scripts/smoke_lab_gateway.py
```
