#!/usr/bin/env python3
"""Publica un APK validado y prepara los campos OTA locales; no modifica el Gist."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

REPO = 'Ronald-Roa/magia-releases'
JSON_PATH = Path(__file__).resolve().with_name('devices.json')


def run(args):
    return subprocess.run([str(x) for x in args], check=True, capture_output=True, text=True).stdout


def inspect_apk(apk, version_name):
    run(['apksigner', 'verify', apk])
    badge = run(['aapt', 'dump', 'badging', apk])
    match = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badge)
    if not match or match[1] != 'com.xuper.netxxus':
        raise ValueError('El APK no corresponde al paquete de Magia APK')
    code, name = int(match[2]), match[3]
    if name != version_name:
        raise ValueError(f'La versión solicitada {version_name} no coincide con el APK: {name}')
    with zipfile.ZipFile(apk) as z:
        try:
            metadata = json.loads(z.read('assets/magia-ota.json'))
        except KeyError:
            raise ValueError('APK antiguo con versión OTA fija: recompilar con build.py --version-code y --version-name')
    expected = {'version_source': 'android_package_info', 'version_code': code, 'version_name': name}
    if any(metadata.get(key) != value for key, value in expected.items()) or (
            metadata.get('package_name', 'com.xuper.netxxus') != 'com.xuper.netxxus') or (
            metadata.get('ota_gist_key', 'xuper_ota') != 'xuper_ota'):
        raise ValueError('Los metadatos OTA no coinciden con el manifiesto del APK')
    if code <= 43404:
        raise ValueError('La versión debe superar la compilación instalada 43404')
    return code, name


def select_asset(assets, size, digest):
    matches = [a for a in assets if a['name'] == 'Magia.apk']
    if len(matches) != 1 or matches[0]['size'] != size:
        raise ValueError('GitHub no confirmó el asset Magia.apk con el tamaño esperado')
    asset = matches[0]
    if asset.get('digest') and asset['digest'] != 'sha256:' + digest:
        raise ValueError('El SHA256 de GitHub no coincide con el archivo subido')
    return asset['browser_download_url']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version_name')
    parser.add_argument('apk', type=Path)
    parser.add_argument('--notes', default='Actualización de Magia APK.')
    parser.add_argument('--dry-run', action='store_true', help='Validar sin publicar ni cambiar archivos')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9][0-9A-Za-z._-]*', args.version_name):
        parser.error('Nombre de versión no válido para el tag')
    # Immutable snapshot: validate and upload exactly the same bytes.
    with tempfile.TemporaryDirectory(prefix='magia-publish-') as temp:
        apk = Path(temp) / 'Magia.apk'
        shutil.copyfile(args.apk, apk)
        code, name = inspect_apk(apk, args.version_name)
        size = apk.stat().st_size
        digest = hashlib.sha256(apk.read_bytes()).hexdigest()
        tag = 'magia-apk-v' + name
        fields = dict(apk_latest_version=code, apk_version_name=name,
                      apk_sha256=digest, apk_size_bytes=size, apk_changelog=args.notes)
        if args.dry_run:
            print(json.dumps({'tag': tag, 'asset': apk.name, **fields}, indent=2, ensure_ascii=False))
            return
        notes = Path(temp) / 'notes.md'
        notes.write_text(args.notes)
        run(['gh', 'release', 'create', tag, '--repo', REPO, '--draft',
             '--title', f'Magia APK {name}', '--notes-file', notes])
        run(['gh', 'release', 'upload', tag, apk, '--repo', REPO])
        # Draft releases may not resolve by tag and have provisional asset URLs.
        view = json.loads(run(['gh', 'release', 'view', tag, '--repo', REPO, '--json', 'apiUrl']))
        release = json.loads(run(['gh', 'api', view['apiUrl']]))
        select_asset(release['assets'], size, digest)
        run(['gh', 'release', 'edit', tag, '--repo', REPO, '--draft=false', '--latest=false'])
        release = json.loads(run(['gh', 'api', view['apiUrl']]))
        if release.get('draft'):
            raise ValueError('El release sigue en borrador')
        fields['apk_apk_url'] = select_asset(release['assets'], size, digest)
        staging = JSON_PATH.with_suffix('.json.tmp')
        staging.write_text(json.dumps(fields, indent=2, ensure_ascii=False) + '\n')
        staging.replace(JSON_PATH)
        print(f'Release publicado: {tag}. Campos OTA preparados en {JSON_PATH}.')
        print('Ejecuta ota_gist.py para anunciar la actualización.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'ERROR: {exc}\n{getattr(exc, "stderr", "") or ""}')
