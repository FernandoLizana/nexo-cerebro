# Emparejamiento

El gateway no escanea la red y no escucha en `0.0.0.0`.

```bash
nexo-lab-gateway start --enable-mobile-lab --acknowledge-risks --host 192.168.1.20 --port 8767 --foreground
```

Imprime un JSON con: versión, IP explícita, puerto, fingerprint SHA-256 del certificado, código de un solo uso, expiración (120 s) y lab id. No lleva secretos permanentes.

1. El celular pega ese JSON y envía `POST /v1/pair` firmado (public key hex, sin privada).
2. El código se invalida. Un segundo uso se rechaza.
3. El PC debe aprobar: `nexo-lab-gateway approve <node_id>`.
4. Heartbeats, eventos y experiencias requieren nodo `approved`, firma válida y nonce nuevo.

Loopback solo con `--allow-loopback` (tests o `adb reverse`).

## Validación sin UI del emulador

Si el AVD no llega a `adb devices` (GPU/OpenGL colgado en headless), igual podés probar el contrato hub:

```bash
python -m services.presence.hub   # genera data/presence_hub/token.txt
python scripts/proof_presence_greet.py   # 401 sin token, 200 con token + Host 10.0.2.2
python scripts/proof_dyad_autonomy.py
```

Inyección de prefs cuando el emulador sí esté `device`:

```bash
adb reverse tcp:8770 tcp:8770
adb install -r apps/android-node/app/build/outputs/apk/debug/app-debug.apk
python scripts/adb_inject_presence_prefs.py --all-emulators
```

Los POST a `http://127.0.0.1:8770` (o emulador) requieren cabecera `X-Nexo-Presence-Token`.

1. Arrancá el hub: `python -m services.presence.hub` (crea `data/presence_hub/token.txt` si no hay `NEXO_PRESENCE_TOKEN`).
2. En la app Android, pegá ese token en el campo **Token del hub**.
3. Preferí `http://127.0.0.1:8770` con `adb reverse tcp:8770 tcp:8770`, o `http://10.0.2.2:8770` (alias lab del emulador).

Sin token, el hub responde 401; eso no es desconexión del personaje.

## Teléfono físico

- Configurá la URL del hub/gateway a la **IP LAN del PC** (misma Wi‑Fi), no la del emulador.
- Cleartext HTTP solo para dominios de lab listados en `network_security_config.xml`. En producción de lab usá **TLS** (`nexo-lab-gateway`) con pinning del fingerprint del JSON de pairing.
- Alternativa USB: `adb reverse tcp:8767 tcp:8767` y gateway en `127.0.0.1 --allow-loopback`.
- Smoke: `python scripts/smoke_lab_gateway.py` (loopback; no bindea interfaces públicas).

Ver también [`NEXO_INSTALL.md`](NEXO_INSTALL.md) § Teléfono físico.
