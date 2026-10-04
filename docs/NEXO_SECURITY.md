# NEXO — seguridad (GitHub readiness)

**Alcance:** controles implementados en el lab. **No** es una certificación de producción ni un modelo multi-tenant IAM.

Complementa [`../SECURITY.md`](../SECURITY.md), [`NEXO_SWARM_SECURITY_MODEL.md`](NEXO_SWARM_SECURITY_MODEL.md) y la serie [`MOBILE_SECURITY.md`](MOBILE_SECURITY.md).

---

## Controles verificados (hardening)

| Control | Qué hace | Dónde |
|---------|----------|--------|
| **Clave registrada** | En nodos *approved*, la clave del envelope debe coincidir con la registrada; una clave solo en el mensaje no basta | `services/lab_gateway/verify.py` |
| **XSS / DOM** | UIs del hub/dashboard usan `textContent` (no `innerHTML` para datos de red) | `services/presence/static/*.js`, dashboard |
| **BrowserPolicy** | Solo orígenes loopback por defecto; rechaza spoofs tipo `localhost.attacker.invalid` y `user@host` | `nexo_qa/browser/policy.py` |
| **BeingStore / LocalMemoryStore** | `being_id` seguro; bloqueo de `../` y path escape | `services/being/store.py`, `services/memory/local/store.py` |
| **STOP** | Kill switch cooperativa; jobs se cancelan; sin anti-uninstall | `nexo-node stop`, Android STOP |
| **Artifact secrets** | El ZIP de release rechaza nombres/sufijos sensibles (`.env`, `.pem`, `pairing`, keystore, …) | `scripts/build_release_artifact.py` |
| **Presence token** | Mutaciones del hub exigen `X-Nexo-Presence-Token` (≥16 chars); Origin loopback si el browser envía Origin | `services/presence/auth.py` |
| **Android cleartext** | Cleartext **global off**; permitido solo para hub lab local (`10.0.2.2`, `127.0.0.1`, `localhost`) | `apps/android-node/.../network_security_config.xml` |
| **Cuarentena** | Experiencias remotas / móviles no auto-promueven | dyad_learning, experience, gateway |

Tests de regresión: `tests/test_nexo_hardening.py`, `tests/test_node_stop.py`, `tests/test_presence_four.py`, `tests/mobile_contract/`.

---

## Presence token

- Archivo por defecto: `data/presence_hub/token.txt` (gitignored).
- Override: `NEXO_PRESENCE_TOKEN` o `NEXO_PRESENCE_TOKEN_FILE`.
- Header: `X-Nexo-Presence-Token`.
- Es un secreto **local de laboratorio**, no un sistema de cuentas.

Si el token se filtró (historial de chat, captura, commit accidental): **rotar** (borrar el archivo / regenerar env) y reiniciar el hub.

---

## Artefacto de release

```bash
python scripts/build_release_artifact.py
```

(No hay `--help`; el script construye y valida.)

Excluye `data/brain_state/`, presence hub, node shelf, keystores, `.env`, rutas personales en resultados, etc. Si la validación posterior detecta secretos o paths personales, **borra el ZIP** y falla.

Ver resultado actual en [`NEXO_INSTALL.md`](NEXO_INSTALL.md) § artefacto.

---

## Android / firmas

- No hay `.jks` / keystore de release en el repo.
- `local.properties` y `keystore.properties` no se versionan.
- Emparejamiento: JSON de un solo uso; sin cámara (política). Detalle: [`MOBILE_PAIRING.md`](MOBILE_PAIRING.md), [`MOBILE_LIMITATIONS.md`](MOBILE_LIMITATIONS.md).

---

## Pasos del owner (checklist)

1. **Si hubo filtración en historial** (token, `.pem`, pairing code, dashboard token): rotar secretos; invalidar nodos pendientes; no reutilizar códigos QR/JSON vencidos.
2. **Definir tokens fuera del git:** `NEXO_PRESENCE_TOKEN`, token de dashboard (`data/nexo_dashboard/`), variables de keystore Android fuera del árbol.
3. **No commitear** `data/brain_state/`, `data/presence_hub/`, `data/nexo_node*/`, `.env`, `*.pem`, `*.jks`, `local.properties`.
4. **Gateway móvil:** solo con flags explícitos; TLS; aprobar nodos a mano (`nexo-lab-gateway approve`).
5. **STOP** antes de desinstalar o compartir la máquina de lab.
6. Antes de push público: `python scripts/validate_pre_release.py` (o Docker validation).

---

## CI (nota corta)

- Workflow: `.github/workflows/tests.yml`.
- Instalación base: `pip install -e ".[dev]"`.
- Pasos BrowserWorld usan `pip install -e ".[browser]"` (extra referenciado por CI; debe existir en `pyproject.toml` extras — si falta, esos jobs fallan o hay que añadir el extra).
- **Política:** una corrida que colecta **cero tests** debe fallar el job (no reportar éxito vacío). Configurar o assert explícito de `collected > 0`; no tratar `continue-on-error` de P2–P9 como “verde de release”.

Prohibiciones duras (escaneo, gusanos, shell remoto, …): [`../SECURITY.md`](../SECURITY.md).
