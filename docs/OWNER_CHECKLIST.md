# Checklist del propietario (acciones que no puede automatizar el agente)

Marcá cuando completes. El código y las pruebas de laboratorio ya están en el repo.

## Publicación GitHub

- [ ] Revisar diff en `nexo-collective-swarm` (o rama actual)
- [ ] **No** commitear: `data/brain_state/`, `data/presence_hub/`, tokens, `.pem`, `local.properties`, APK firmados
- [ ] Sí incluir: `apps/android-node/gradlew*`, `gradle/wrapper/`, código, docs, tests
- [ ] Commit + push cuando quieras
- [ ] Crear release a partir de `dist/NEXO_REPRODUCIBLE_*.zip` regenerado desde árbol limpio

## Secretos

- [ ] Si el historial remoto/local pudo filtrar claves o tokens → **rotar** (no reescribir historial)
- [ ] Guardar `data/presence_hub/token.txt` fuera de Git (ya está en `.gitignore`)

## Android en emuladores (agente puede inyectar prefs; vos confirmás UI)

- [x] APK debug compilado e instalado (sesión agente; regenerar si cambias código)
- [x] Auto-GREET vía Intent extras (`hub_url`, `presence_token`, `auto_greet`) verificado en emulador headless
- [ ] Abrir Cerebro / Nodo en UI y confirmar visualmente URL + token
- [ ] Segundo AVD (`Medium_Phone_B`) si querés dos teléfonos a la vez (libera disco antes)

## Teléfono físico (requiere tu hardware)

- [ ] USB debugging o misma Wi‑Fi que el PC
- [ ] Configurar URL `http://<IP-LAN-PC>:8770` + token (o TLS lab_gateway)
- [ ] Probar GREET y STOP NEXO NODE

## Contenido de terceros

- [ ] Confirmar que el PDF médico de `data/library/` no se publica (excluido del artefacto)
- [ ] Revisar condiciones de redistribución si algún día lo incluís aparte

## Referencias

- `docs/NEXO_INSTALL.md`, `docs/NEXO_SECURITY.md`, `docs/MOBILE_PAIRING.md`
- Scripts: `scripts/proof_dyad_autonomy.py`, `scripts/proof_presence_greet.py`, `scripts/adb_inject_presence_prefs.py`
