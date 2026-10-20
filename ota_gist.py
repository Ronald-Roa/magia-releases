#!/usr/bin/env python3
"""Publica exclusivamente los seis campos OTA de Magia APK en el Gist compartido."""
import argparse
import json
from pathlib import Path
import re
import subprocess

GIST = '8e16061ce8976aa571525f2c5408f7bd'
JSON_PATH = Path(__file__).resolve().with_name('devices.json')
FIELDS = {'apk_latest_version', 'apk_version_name', 'apk_apk_url',
          'apk_sha256', 'apk_size_bytes', 'apk_changelog'}


def merge_fields(current, local):
    if set(local) != FIELDS:
        raise ValueError('devices.json debe contener exclusivamente los seis campos OTA apk_*')
    version = local['apk_latest_version']
    if type(version) is not int or version <= 43404:
        raise ValueError('Publicar primero un APK nuevo con versión OTA sincronizada')
    if version < current.get('apk_latest_version', 0):
        raise ValueError('No se permite anunciar una versión anterior a la del Gist')
    if not isinstance(local['apk_sha256'], str) or not re.fullmatch(r'[a-f0-9]{64}', local['apk_sha256']):
        raise ValueError('SHA256 no válido')
    if type(local['apk_size_bytes']) is not int or local['apk_size_bytes'] <= 0:
        raise ValueError('Tamaño de APK no válido')
    if not isinstance(local['apk_apk_url'], str) or not local['apk_apk_url'].startswith(
            'https://github.com/Ronald-Roa/magia-releases/releases/download/'):
        raise ValueError('URL fuera del repositorio de releases')
    if not isinstance(local['apk_version_name'], str) or not local['apk_version_name']:
        raise ValueError('Nombre de versión ausente')
    if not isinstance(local['apk_changelog'], str):
        raise ValueError('Changelog no válido')
    if version == current.get('apk_latest_version') and any(
            current.get(k) != local[k] for k in FIELDS - {'apk_changelog'}):
        raise ValueError('Para cambiar el APK publicado hay que aumentar versionCode')
    return {**current, **{key: local[key] for key in FIELDS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Leer y validar sin modificar el Gist')
    args = parser.parse_args()
    local = json.loads(JSON_PATH.read_text())
    response = subprocess.run(['gh', 'api', f'gists/{GIST}'],
                              check=True, capture_output=True, text=True)
    gist = json.loads(response.stdout)
    remote = gist['files']['devices.json']
    if remote.get('truncated'):
        raise ValueError('GitHub devolvió devices.json truncado; no se modificará el Gist')
    merged = merge_fields(json.loads(remote['content']), local)
    if args.dry_run:
        print(json.dumps({k: merged[k] for k in sorted(FIELDS)}, indent=2, ensure_ascii=False))
        return
    payload = {'files': {'devices.json': {'content': json.dumps(merged, indent=2, ensure_ascii=False)}}}
    subprocess.run(['gh', 'api', f'gists/{GIST}', '-X', 'PATCH', '--input', '-'],
                   input=json.dumps(payload), text=True, check=True, capture_output=True)
    print('Gist actualizado: solo campos OTA de Magia APK.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'ERROR: {exc}\n{getattr(exc, "stderr", "") or ""}')
