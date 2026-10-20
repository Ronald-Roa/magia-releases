# Actualizaciones de Magia APK

Repositorio: `Ronald-Roa/magia-releases`.
Gist compartido: `8e16061ce8976aa571525f2c5408f7bd`.

## Versión única para Android y OTA

Las nuevas compilaciones consultan `PackageInfo.versionCode` en el dispositivo.
El publicador lee ese mismo número del manifiesto del APK y lo escribe en
`apk_latest_version`. No se calcula a partir del nombre de versión.

La APK `Magia_OTA_43410_Fast.apk` tiene `versionCode=43410`. Su clase
`com.magia.auth.MagiaWorker` compara `apk_latest_version` del Gist con ese valor
y muestra el aviso a los Machine ID autorizados. La versión pública anunciada
es **4.34.23 (43423)**, con el mismo paquete y certificado de firma.

La Build 43423 instalada usa el canal `xuper_ota` y actualmente omite el diálogo
de actualización si arranca con una sesión guardada. Corregir ese flujo en una
build posterior antes de prometer OTA automática desde 43423.

## Compilar y validar sin publicar

```sh
python3 /root/xuper-magia-build/build.py --version-code 43423 --version-name 4.34.23
python3 /root/xuper-magia-ota/ota_publish.py 4.34.23 /storage/emulated/0/Download/Magia_OTA_43423.apk --dry-run
```

El build recompila el Java de autorización, lo integra con el smali recuperado,
actualiza versionCode/versionName, conserva el aspecto visual, alinea y firma.
El APK contiene `assets/magia-ota.json` para verificar que utiliza la numeración
nueva. Se rechazan APK antiguos sin ese marcador o con números inconsistentes.

## Publicar una actualización

Estos comandos modifican GitHub; ejecutarlos cuando se quiera anunciar la versión:

```sh
python3 /root/xuper-magia-ota/ota_publish.py 4.34.23 /storage/emulated/0/Download/Magia_OTA_43423.apk --notes 'Reproducción VOD directa.'
python3 /root/xuper-magia-ota/ota_gist.py --dry-run
python3 /root/xuper-magia-ota/ota_gist.py
```

El publicador toma una copia del APK, valida su firma, paquete y versión, crea
un borrador con tag `magia-apk-v4.34.23`, sube siempre el archivo como `Magia.apk`,
verifica el asset devuelto por GitHub y utiliza su `browser_download_url` real.
Solo después publica el release y guarda los campos en devices.json local.
No marca este release como Latest, para no desplazar los releases de Magia Web.
Si falla una subida, el borrador queda sin anunciar y devices.json no se modifica.

`ota_gist.py` combina únicamente estos seis campos, rechazando cualquier otro:
`apk_latest_version`, `apk_version_name`, `apk_apk_url`, `apk_sha256`,
`apk_size_bytes`, `apk_changelog`. Conserva los demás campos del Gist, incluida
la autorización compartida, y rechaza versiones anteriores o APK diferentes con
el mismo número. No cambiar el Gist desde otros paneles simultáneamente al publicar,
pues la combinación es una operación de lectura seguida de escritura.

La aplicación consulta al abrir la pantalla inicial, comprueba autorización y,
si hay una versión superior, ofrece descargarla. La instalación requiere la
confirmación de Android. El cliente actual abre la URL en el navegador: no es
una instalación silenciosa ni un verificador de la descarga por SHA256.

## Pruebas

```sh
cd /root/xuper-magia-ota
python3 -m unittest -v test_ota
```

Las pruebas simulan GitHub; no crean releases ni alteran el Gist.
La gestión de dispositivos continúa mediante `auth_device.py` o el panel habitual.
