#!/usr/bin/env python3
"""Autorizar/desautorizar dispositivos en el gist compartido de Magia.

Los authorized_devices son compartidos entre Magia Web y Magia APK.
Este script modifica directamente el gist sin pisar los otros campos.

Uso:
  python3 auth_device.py list
  python3 auth_device.py add    <DEVICE_ID> [--nombre "Juan" --cat premium --vence 2026-12-31]
  python3 auth_device.py remove <DEVICE_ID>
"""
import sys, json, subprocess

GIST = "8e16061ce8976aa571525f2c5408f7bd"

def fetch_gist():
    r = subprocess.run(["gh", "api", f"gists/{GIST}"], capture_output=True, text=True)
    if r.returncode != 0:
        print("ERROR al obtener gist:", r.stderr[:300]); sys.exit(1)
    gist_data = json.loads(r.stdout)
    return json.loads(gist_data["files"]["devices.json"]["content"])

def push_gist(data):
    content = json.dumps(data, indent=2, ensure_ascii=False)
    payload = json.dumps({
        "description": "Canal OTA de Magia Web (metadata pública de versiones)",
        "files": {"devices.json": {"content": content}},
    })
    r = subprocess.run(
        ["gh", "api", f"gists/{GIST}", "-X", "PATCH", "--input", "-"],
        input=payload.encode(), capture_output=True
    )
    if r.returncode == 0:
        print("✅ Gist actualizado.")
    else:
        print("ERROR:", r.stderr.decode()[:300])
    return r.returncode

cmd  = sys.argv[1] if len(sys.argv) > 1 else "list"
data = fetch_gist()

if cmd == "list":
    devs = data.get("authorized_devices", [])
    print(f"Dispositivos autorizados ({len(devs)}) — gist {GIST}:")
    for d in devs:
        nota   = data.get("notas_de_clientes", {}).get(d, {})
        nombre = nota.get("nombre", "")
        cat    = nota.get("categoria", "")
        vence  = nota.get("vence", "")
        print(f"  {d}  {nombre}  [{cat}]  vence:{vence}")

elif cmd == "add":
    device = sys.argv[2].upper()
    args   = sys.argv[3:]
    nombre = cat = vence = ""
    for i, a in enumerate(args):
        if a == "--nombre" and i+1 < len(args): nombre = args[i+1]
        if a == "--cat"    and i+1 < len(args): cat    = args[i+1]
        if a == "--vence"  and i+1 < len(args): vence  = args[i+1]

    devs = data.setdefault("authorized_devices", [])
    if device not in devs:
        devs.append(device)
        print(f"+ Autorizado: {device}")
    else:
        print(f"~ Ya existía: {device}")

    if nombre or cat or vence:
        notas = data.setdefault("notas_de_clientes", {})
        notas[device] = {"nombre": nombre, "categoria": cat, "vence": vence}

    sys.exit(push_gist(data))

elif cmd == "remove":
    device = sys.argv[2].upper()
    devs   = data.get("authorized_devices", [])
    if device in devs:
        devs.remove(device)
        data.get("notas_de_clientes", {}).pop(device, None)
        print(f"- Removido: {device}")
        sys.exit(push_gist(data))
    else:
        print(f"No encontrado: {device}")

else:
    print("Uso: auth_device.py [add|remove|list] ...")
