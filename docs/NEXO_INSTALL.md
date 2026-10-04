# NEXO — instalación, emparejamiento, stop y recuperación

**Estado:** guía de laboratorio en máquina del owner. **No** instalación silenciosa ni SaaS gestionado.

Versión de referencia: paquete `nexo-cerebro` **0.3.0** (`pyproject.toml`). El artefacto de release debe coincidir con ese número; comprueba el manifest al empaquetar.

---

## Checklist del propietario

Acciones que requieren tu cuenta/dispositivo: [`docs/OWNER_CHECKLIST.md`](docs/OWNER_CHECKLIST.md).

- Python **3.11+**
- Windows 10/11, Linux o macOS (dev)
- Opcional: Docker 24+ ([`DOCKER_VALIDATION.md`](DOCKER_VALIDATION.md))
- Móvil: JDK 17 + Android SDK (ver docs móviles abajo)

---

## Instalación

```bash
python -m pip install -e ".[dev]"
python -c "import nexo, services.node, services.lab; print('ok')"
```

Extras:

| Extra | Uso |
|-------|-----|
| `.[dev]` | pytest / desarrollo (requerido en CI base) |
| `.[browser]` | Playwright / BrowserWorld (CI opcional; debe estar definido en `pyproject.toml`) |
| `.[gpu]` | CuPy (solo paths GPU legacy; no requerido para Swarm) |

---

## Configuración mínima

```bash
# Nodo local
nexo-node start --name lab-a --cpu-max 40 --ram-max-mb 1024

# Dashboard solo loopback
nexo-dashboard --host 127.0.0.1 --port 8765
# Token: data/nexo_dashboard/ (no commitear)

# Presence hub (demo visual local)
# Token: data/presence_hub/token.txt o NEXO_PRESENCE_TOKEN
python -m services.presence.hub
```

Overrides útiles: `NEXO_*` (ver README). Config YAML: `configs/swarm/`.

Demo Flask legacy (didáctico, no control plane Swarm):

```bash
python app.py
# http://127.0.0.1:5000
```

---

## Emparejamiento móvil

Documentación canónica (no duplicar aquí el protocolo):

| Doc | Contenido |
|-----|-----------|
| [`MOBILE_NODE_ARCHITECTURE.md`](MOBILE_NODE_ARCHITECTURE.md) | Capas gateway / APK / contratos |
| [`MOBILE_PAIRING.md`](MOBILE_PAIRING.md) | JSON de un solo uso, approve, heartbeats |
| [`MOBILE_SECURITY.md`](MOBILE_SECURITY.md) | TLS, jobs, cuarentena, replay |
| [`MOBILE_PRIVACY.md`](MOBILE_PRIVACY.md) | Permisos y datos |
| [`MOBILE_TESTING.md`](MOBILE_TESTING.md) | Cómo probar |
| [`MOBILE_LIMITATIONS.md`](MOBILE_LIMITATIONS.md) | Keystore, huecos conocidos |
| [`../apps/android-node/README.md`](../apps/android-node/README.md) | Build APK debug |

Resumen operativo:

```bash
nexo-lab-gateway start --enable-mobile-lab --acknowledge-risks --host <IP-LAN> --port 8767 --foreground
# Pegar JSON en el teléfono → POST /v1/pair
nexo-lab-gateway approve <node_id>
```

Smoke (solo loopback, no interfaz pública):

```bash
python scripts/smoke_lab_gateway.py
```

Comprueba que el cert lab existe y tiene fingerprint SHA-256; arranca y para en `127.0.0.1`.

---

## Teléfono físico

1. **URL del hub / gateway:** en la UI del APK, configurá la IP **LAN del PC** (p. ej. `192.168.1.20`), no `10.0.2.2` (eso es emulador).
2. **Cleartext:** el `network_security_config` solo permite HTTP claro para dominios de lab (`10.0.2.2`, `127.0.0.1`, `localhost`). En teléfono físico **no** abras cleartext arbitrario a toda la LAN; para producción o red real usá el **TLS lab gateway** (`nexo-lab-gateway`, pinning por fingerprint).
3. **Alternativa USB:** `adb reverse tcp:8767 tcp:8767` (y/o el puerto del presence hub) y apuntá el teléfono a `127.0.0.1` con `--allow-loopback` en el gateway. El gateway **nunca** debe bindear `0.0.0.0` ni IPs públicas.
4. Emparejá con el JSON que imprime `nexo-lab-gateway start … --host <IP-LAN>` (fingerprint + código de un solo uso).

Detalle de pairing: [`MOBILE_PAIRING.md`](MOBILE_PAIRING.md). Contenido de terceros / PDFs: [`NEXO_THIRD_PARTY_CONTENT.md`](NEXO_THIRD_PARTY_CONTENT.md).

---

## Stop (kill switch)

```bash
nexo-node stop --data-dir data/nexo_node
# o
nexo-ctl stop dashboard
```

En Android: acción **STOP NEXO NODE** (detiene el foreground service; no se auto-revive al boot).

---

## Recuperación

| Situación | Acción |
|-----------|--------|
| Token presence / dashboard filtrado | Borrar `token.txt`, regenerar env, reiniciar servicio |
| Nodo corrupto / jobs colgados | `nexo-node stop`, inspeccionar `data/nexo_node*/`, volver a `start` |
| Aprendizaje malo promovido | Rollback con `nexo-learn` (promote es manual; no hay undo mágico del Core) |
| Emparejamiento fallido | Nuevo pairing code (TTL corto); no reusar JSON vencido |
| Estado brain demo | No restaurar desde git: `data/brain_state/` es local; backup del owner si hace falta |
| Artefacto ZIP inválido | El script elimina el ZIP si hay secretos/paths personales; limpiar demos `.pem` / scripts con rutas absolutas y reintentar |

---

## Artefacto reproducible

```bash
python scripts/build_release_artifact.py
```

Salida esperada: `dist/NEXO_REPRODUCIBLE_<ver>.zip`, `dist/SHA256SUMS.txt`, `dist/artifact_manifest.json`.

### Resultado en esta preparación (doc)

Intentado al documentar GitHub readiness: el build **falló** la validación posterior con:

- `personal_paths_in_zip` — al menos un archivo incluido contenía marcadores de ruta personal (p. ej. bajo `scripts/`).
- `secrets_in_zip` — archivos `.pem` de demo bajo `data/` entraron al conjunto empaquetable.

**No** se publica hash de un ZIP válido en este ciclo. Corregir exclusiones / limpiar demos sensibles y volver a ejecutar el script. El ZIP fallido no debe distribuirse.

Verificación aparte: `python -m scripts.verify_artifact` / `python scripts/validate_pre_release.py`.

---

## CI (nota)

Ver [`NEXO_SECURITY.md`](NEXO_SECURITY.md) § CI: extras `dev`/`browser`, y **fallar si se colectan cero tests**.

---

## Siguiente lectura

- Arquitectura: [`NEXO_ARCHITECTURE.md`](NEXO_ARCHITECTURE.md)
- Seguridad: [`NEXO_SECURITY.md`](NEXO_SECURITY.md)
- README raíz: instalación Swarm + validación pre-push
