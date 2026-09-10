#!/usr/bin/env python3
"""Publicar release de Magia APK en Ronald-Roa/magia-releases.

Tag pattern : magia-apk-v<versionName>   (ej. magia-apk-v1.0)
Asset subido: Magia.apk

Uso:
  python3 ota_publish.py <versionName> [<apk_path>] [--notes "..."]

Ejemplo:
  python3 ota_publish.py 1.0
  python3 ota_publish.py 1.1 /storage/emulated/0/Download/Magia_final.apk
"""
import subprocess, sys, time, hashlib, os, json

VERSION   = sys.argv[1] if len(sys.argv) > 1 else "1.0"
APK       = sys.argv[2] if len(sys.argv) > 2 else f"/storage/emulated/0/Download/Magia_final.apk"
TAG       = f"magia-apk-v{VERSION}"
TITLE     = f"Magia APK {TAG}"
REPO      = "Ronald-Roa/magia-releases"
JSON_PATH = "/root/xuper-magia-ota/devices.json"

# Parse --notes from args
notes = f"Magia APK versión {VERSION}."
for i, arg in enumerate(sys.argv):
    if arg == "--notes" and i + 1 < len(sys.argv):
        notes = sys.argv[i + 1]

def run(cmd):
    print("> " + " ".join(cmd))
    return subprocess.run(cmd).returncode

# ── Compute sha256 + size ──────────────────────────────────────────────────
print(f"\n📦 APK: {APK}")
sha256 = hashlib.sha256(open(APK, "rb").read()).hexdigest()
size   = os.path.getsize(APK)
print(f"   sha256: {sha256}")
print(f"   size  : {size:,} bytes\n")

# ── 1. Create release ──────────────────────────────────────────────────────
rc = run(["gh", "release", "create", TAG,
          "--repo", REPO, "--title", TITLE,
          "--notes", notes, "--latest"])
if rc != 0:
    sys.exit(rc)

# ── 2. Upload APK (retry 3x) ───────────────────────────────────────────────
for attempt in range(3):
    rc = run(["gh", "release", "upload", TAG, APK,
              "--repo", REPO, "--clobber"])
    if rc == 0:
        break
    print(f"  Upload failed (attempt {attempt+1}), retrying in 10s...")
    time.sleep(10)

if rc != 0:
    sys.exit(rc)

# ── 3. Update devices.json ─────────────────────────────────────────────────
apk_url = f"https://github.com/{REPO}/releases/download/{TAG}/Magia.apk"
build   = int(VERSION.replace(".", "").ljust(6, "0")[:6]) if VERSION.replace(".", "").isdigit() else 1

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Use apk_* prefix to coexist with Magia Web fields in the shared gist
data["apk_latest_version"] = build
data["apk_version_name"]   = f"{VERSION} ({build})"
data["apk_apk_url"]        = apk_url
data["apk_sha256"]         = sha256
data["apk_size_bytes"]     = size
data["apk_changelog"]      = notes

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✅ devices.json actualizado → {JSON_PATH}")
print(f"   Corre ota_gist.py para publicar al gist.\n")
