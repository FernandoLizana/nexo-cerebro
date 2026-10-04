# Limitaciones reales

- El SDK está en `%LOCALAPPDATA%\Android\Sdk` (platforms 34/35, AVD `Medium_Phone`, imagen android-36). El JBR de Android Studio es JDK 21. El APK debug se compiló e instaló en ese emulador. Java 26 del sistema no sirve para Gradle; hay que usar el JBR.
- No hay emulador, así que no hay instalación ADB ni prueba de airplane mode en dispositivo.
- El escaneo de cámara del QR no está implementado a propósito: contradice la prohibición de permiso de cámara. El emparejamiento es el JSON pegado.
- Ed25519 no exportable en Android Keystore no está comprobado aquí. La v1 no afirma respaldo hardware.
- El motor móvil no reproduce el CreatureEngine float del PC. El contrato portable es `creature-mobile-tier0-v1`.
- TextWorld completo del PC no corre en el teléfono. El job solo se acepta si el nodo lo declara; el experimento implementado y con vector dorado es el FSM Tier 0.
- WorkManager está en el Gradle file para tareas diferibles, pero v1 no programa sync en background: no se evade Doze.
- La clave de firma release no se incluye. Para un release local:

```bash
keytool -genkeypair -v -keystore %USERPROFILE%\.nexo\nexo-node-release.jks -alias nexo -keyalg RSA -keysize 2048 -validity 3650
```

Luego definir `NEXO_RELEASE_STORE` fuera del repo. No commitear el `.jks`.
