# Magia APK — OTA Infrastructure

## Repositorio y gist

- **Repo de releases**: `Ronald-Roa/magia-releases`
- **Gist compartido** (mismo que Magia Web): `8e16061ce8976aa571525f2c5408f7bd`
  - Los campos de Magia Web (`latest_version`, `apk_url`, `authorized_devices`, etc.) no se tocan
  - Los campos de Magia APK tienen prefijo `apk_`: `apk_latest_version`, `apk_apk_url`, `apk_changelog`
  - `authorized_devices` es compartido: si un dispositivo está autorizado, accede a AMBAS apps

## Flujo de publicación

```
1. Compilar / parchear el APK → Magia_final.apk
2. python3 ota_publish.py <versionName> [<apk_path>] [--notes "..."]
   → sube a Ronald-Roa/magia-releases  tag: magia-apk-v<ver>  asset: Magia.apk
   → actualiza devices.json local (campos apk_*)
3. python3 ota_gist.py
   → merge los campos apk_* al gist compartido (sin pisar campos de Magia Web)
```

## Gestión de dispositivos

Los dispositivos se gestionan igual que siempre desde admin_panel.html
o desde la línea de comandos con Magia Web. Son compartidos entre apps.

```bash
# Consultar directamente el gist
gh gist view 8e16061ce8976aa571525f2c5408f7bd

# Añadir dispositivo al gist (modifica la sección authorized_devices)
python3 auth_device.py add <DEVICE_ID> [--nombre "Nombre" --cat premium --vence 2026-12-31]
python3 auth_device.py remove <DEVICE_ID>
python3 auth_device.py list

# auth_device.py trabaja directamente sobre el gist (no local)
```

## Estructura devices.json (local — solo campos APK)

```json
{
  "apk_latest_version": 1,
  "apk_version_name": "1.0 (1)",
  "apk_apk_url": "https://github.com/Ronald-Roa/magia-releases/releases/download/magia-apk-v1.0/Magia.apk",
  "apk_sha256": "...",
  "apk_size_bytes": 0,
  "apk_changelog": "..."
}
```

## Campos en el gist compartido

```
# Campos de Magia Web (no modificar desde aquí):
  latest_version, version_name, apk_url, sha256, size_bytes, changelog

# Campos de Magia APK (gestionados por estos scripts):
  apk_latest_version, apk_version_name, apk_apk_url, apk_sha256, apk_size_bytes, apk_changelog

# Compartido entre ambas apps:
  authorized_devices, notas_de_clientes
```
