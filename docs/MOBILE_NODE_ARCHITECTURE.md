# NEXO Node móvil — arquitectura

El coordinador S7 sigue in-process y sin sockets. El enlace del celular es una capa nueva, apagada por defecto.

| Pieza | Ruta | Rol |
|-------|------|-----|
| Contratos | `protocols/mobile/` | Envelope `mobile-v1`, jobs, motor entero compartido |
| Gateway | `services/lab_gateway/` | TLS, QR-payload, doble aprobación, cuarentena |
| APK | `apps/android-node/` | Nodo Kotlin Tier 0 |
| Tests | `tests/mobile_contract/` | Firmas, replay, jobs, cuarentena |

El Core (`nexo/`, MessageBus) no se modifica. El motor float de `services/creature/` tampoco.

## Adaptaciones frente al pedido

1. Las firmas existentes son `nexo-register|…` (Ed25519 sobre texto). El envelope móvil firma JSON canónico sin floats, para que Kotlin y Python coincidan. No se reemplaza el esquema S7.
2. `services/creature/engine.py` usa `random.Random` y floats. Android corre `creature-mobile-tier0-v1` (enteros, xorshift32). El job se llama igual (`RUN_CREATURE_SIMULATION`) pero el payload exige `engine=creature-mobile-tier0-v1`.
3. Escanear QR exige `CAMERA`. La política prohíbe ese permiso. El gateway imprime un JSON de un solo uso; la app lo pega. No hay cámara, contactos, SMS, ubicación, micrófono ni archivos.
4. El certificado TLS del lab es RSA-2048 auto-firmado (7 días). Ed25519 en certificados TLS no es fiable en Android. La identidad del nodo sigue siendo Ed25519.
5. Android Keystore no garantiza Ed25519 no exportable en API 26–32. v1 documenta el hueco y no finge hardware. La clave de firma del APK release no está en el repo.
