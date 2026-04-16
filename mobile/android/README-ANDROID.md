Cómo compilar el APK (Android Studio)

Requisitos:
- Android Studio instalado (incluye SDK y Gradle)
- JDK 11+ (Android Studio instala uno por defecto)

Pasos rápidos:
1. Abre Android Studio -> "Open" -> selecciona la carpeta `mobile/android` del repositorio.
2. Espera a que Gradle sincronice.
3. En el menú Build -> "Build Bundle(s) / APK(s)" -> "Build APK(s)".
4. Cuando acabe, pulsa el enlace que muestra Android Studio para localizar el APK y cópialo al móvil.

Nota:
- La app carga la PWA embebida desde `assets/www/index.html` y por defecto la API usada es `/api/events`. Si pruebas con el servidor Flask local en el mismo dispositivo o emulador, ajusta la URL en la app (campo superior) o sirve la API en una dirección accesible desde el dispositivo.
- Para producción firma el APK con una keystore y configura `signingConfigs` en `app/build.gradle`.
