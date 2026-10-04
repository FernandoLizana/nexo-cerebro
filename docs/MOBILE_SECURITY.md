# Seguridad del nodo móvil

Amenazas: nodo comprometido, job hostil, replay, certificado sustituido, QR viejo, arranque oculto.

Controles:

- Flags `--enable-mobile-lab` y `--acknowledge-risks` o el gateway no arranca.
- TLS 1.2+, `usesCleartextTraffic=false`.
- Pinning: el teléfono envía el fingerprint emparejado; si no coincide, se rechaza.
- Jobs sealed en espíritu: allowlist cerrada. `EXECUTE_SHELL` y el resto de la lista hostil se rechazan antes de encolar.
- Experiencias quedan `QUARANTINED`. No hay promote automático.
- Nonce repetido → 409. Timestamp fuera de 300 s → rechazo.
- Servicio en primer plano solo mientras el experimento corre. `START_NOT_STICKY`: Android no lo revive solo. No hay boot receiver, Device Admin ni accesibilidad.
- Logs del gateway no imprimen la línea HTTP (puede contener el código).

## Teléfono físico (TLS)

En dispositivo real, preferí el gateway TLS con fingerprint del pairing. Cleartext queda limitado a dominios de emulador/loopback; no habilitar cleartext genérico a la LAN. Alternativa: `adb reverse` hacia `127.0.0.1`. Smoke: `python scripts/smoke_lab_gateway.py`.
