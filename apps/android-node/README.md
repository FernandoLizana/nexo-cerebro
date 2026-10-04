# NEXO Node (Android)

Nodo voluntario limitado. No es un control remoto del teléfono.

## Qué hace

Registra una public key, corre Creature Engine `creature-mobile-tier0-v1`, emite eventos, deja experiencias en cuarentena y acepta solo jobs tipados. `STOP NEXO NODE` detiene el foreground service. No arranca al reiniciar.

## Compilar

Hace falta JDK 17 (no Java 26) y un Android SDK con platform 35 y build-tools.

```bash
cd apps/android-node
# local.properties
# sdk.dir=C:\\Users\\<you>\\AppData\\Local\\Android\\Sdk
gradle wrapper
gradlew.bat :app:assembleDebug :app:testDebugUnitTest
```

El APK debug queda en `app/build/outputs/apk/debug/app-debug.apk`.

Instalar, cuando exista un dispositivo:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

No hay clave release en el repositorio. Ver `docs/MOBILE_LIMITATIONS.md`.

Matriz: minSdk 26, target/compile 35. Cleartext solo para dominios de lab explícitos (`10.0.2.2`, `127.0.0.1`, `localhost`); el resto requiere TLS. En teléfono físico configurá la URL del hub (IP LAN del PC) o usá HTTPS. Sin permisos de cámara, contactos, SMS, ubicación, micrófono ni archivos.