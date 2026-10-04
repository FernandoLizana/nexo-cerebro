# Privacidad

El nodo no declara permisos de contactos, SMS, ubicación, cámara, micrófono, almacenamiento amplio ni clipboard.

No lee archivos personales, no sube chats del dueño y no guarda la clave privada en SharedPreferences.

La identidad pública que puede mostrarse es node id, public key hex, versión y capacidades declaradas (`MOBILE_TIER_0`).

Exportar memoria es un acto explícito futuro; v1 solo guarda resumen en cuarentena local (Room) y en el gateway como candidato no promovido.
