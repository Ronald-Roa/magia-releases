#!/usr/bin/env python3
"""Publicar campos APK de Magia en el gist compartido (mismo que Magia Web).

El gist es COMPARTIDO con Magia Web; los campos de Magia Web
(latest_version, apk_url, authorized_devices, etc.) NO se tocan.
Solo se actualizan / añaden los campos con prefijo apk_* en el JSON.

Uso:
  python3 ota_gist.py
"""
import subprocess, sys, json

GIST      = "8e16061ce8976aa571525f2c5408f7bd"
JSON_PATH = "/root/xuper-magia-ota/devices.json"

# Cargar los campos APK locales
with open(JSON_PATH, "r", encoding="utf-8") as f:
    apk_fields = json.load(f)

print(f"📡 Actualizando Magia APK OTA en gist {GIST}")
for k, v in apk_fields.items():
    print(f"   {k}: {v}")

# Obtener contenido actual del gist
r = subprocess.run(["gh", "api", f"gists/{GIST}"], capture_output=True, text=True)
if r.returncode != 0:
    print("ERROR al obtener gist:", r.stderr[:300]); sys.exit(1)

gist_data = json.loads(r.stdout)
current   = json.loads(gist_data["files"]["devices.json"]["content"])

# Merge: solo actualizar campos apk_*
for k, v in apk_fields.items():
    current[k] = v

new_content = json.dumps(current, indent=2, ensure_ascii=False)

payload = json.dumps({
    "description": "Canal OTA de Magia Web (metadata pública de versiones)",
    "files": {"devices.json": {"content": new_content}},
})

cmd = ["gh", "api", f"gists/{GIST}", "-X", "PATCH", "--input", "-"]
print("\n> " + " ".join(cmd))
r = subprocess.run(cmd, input=payload.encode(), capture_output=True)
if r.returncode == 0:
    print("✅ Gist actualizado con campos Magia APK")
else:
    print("ERROR:", r.stderr.decode()[:300])
sys.exit(r.returncode)
