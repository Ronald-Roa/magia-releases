import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ota_gist as gist
import ota_publish as publish


def fields():
    return dict(apk_latest_version=43405, apk_version_name='1.1',
                apk_apk_url='https://github.com/Ronald-Roa/magia-releases/releases/download/magia-apk-v1.1/Magia.apk',
                apk_sha256='a' * 64, apk_size_bytes=123, apk_changelog='Changes')


class GistTests(unittest.TestCase):
    def test_preserves_other_app_and_devices(self):
        current = dict(latest_version=777, apk_url='other.apk', authorized_devices=['ABC123'],
                       notas_de_clientes={'ABC123': {'nombre': 'Example'}}, extra={'x': 1})
        previous = copy.deepcopy(current)
        merged = gist.merge_fields(current, fields())
        for key, value in previous.items():
            self.assertEqual(merged[key], value)
        self.assertEqual(current, previous)

    def test_rejects_foreign_fields(self):
        for key in ['authorized_devices', 'latest_version', 'apk_unknown']:
            with self.subTest(key=key), self.assertRaises(ValueError):
                gist.merge_fields({}, {**fields(), key: []})

    def test_rejects_downgrade(self):
        with self.assertRaises(ValueError):
            gist.merge_fields({'apk_latest_version': 43406}, fields())

    def test_rejects_replacing_same_version(self):
        with self.assertRaises(ValueError):
            gist.merge_fields({**fields(), 'apk_sha256': 'b' * 64}, fields())
        self.assertEqual(gist.merge_fields(fields(), fields()), fields())

    def test_rejects_incomplete_metadata(self):
        for change in [{'apk_sha256': ''}, {'apk_size_bytes': 0}, {'apk_latest_version': 1},
                       {'apk_apk_url': 'http://example.com/other.apk'}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                gist.merge_fields({}, {**fields(), **change})


class PublishTests(unittest.TestCase):
    def test_uses_confirmed_asset_url_and_normalizes_filename(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            apk = temp / 'My custom APK.apk'
            apk.write_bytes(b'APK snapshot')
            digest = hashlib.sha256(apk.read_bytes()).hexdigest()
            target = temp / 'devices.json'
            calls = []
            url = fields()['apk_apk_url']
            def fake_run(args):
                args = [str(x) for x in args]
                calls.append(args)
                if args[:3] == ['gh', 'release', 'upload']:
                    self.assertEqual(Path(args[4]).name, 'Magia.apk')
                    self.assertEqual(Path(args[4]).read_bytes(), apk.read_bytes())
                if args[:3] == ['gh', 'release', 'view']:
                    return json.dumps({'apiUrl': 'repos/example/releases/123'})
                if args[:2] == ['gh', 'api']:
                    return json.dumps({'assets': [{'name': 'Magia.apk', 'size': apk.stat().st_size,
                                       'digest': 'sha256:' + digest, 'browser_download_url': url}]})
                return ''
            with patch.object(publish, 'run', side_effect=fake_run), \
                 patch.object(publish, 'inspect_apk', return_value=(43405, '1.1')), \
                 patch.object(publish, 'JSON_PATH', target), \
                 patch('sys.argv', ['ota_publish.py', '1.1', str(apk)]):
                publish.main()
            result = json.loads(target.read_text())
            self.assertEqual(result['apk_apk_url'], url)
            self.assertEqual(result['apk_latest_version'], 43405)
            self.assertEqual(result['apk_sha256'], digest)
            self.assertEqual(set(result), gist.FIELDS)
            self.assertIn('--draft', calls[0])
            self.assertTrue(any('--draft=false' in call for call in calls))

    def test_rejects_missing_or_wrong_uploaded_asset(self):
        for assets in [[], [{'name': 'Wrong.apk', 'size': 123}],
                       [{'name': 'Magia.apk', 'size': 122}],
                       [{'name': 'Magia.apk', 'size': 123, 'digest': 'sha256:wrong'}]]:
            with self.subTest(assets=assets), self.assertRaises(ValueError):
                publish.select_asset(assets, 123, 'a' * 64)

    def test_rejects_manifest_metadata_mismatch(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            apk = Path(temp) / 'bad.apk'
            with zipfile.ZipFile(apk, 'w') as z:
                z.writestr('assets/magia-ota.json', json.dumps(dict(version_source='android_package_info',
                                  version_code=43406, version_name='1.1')))
            with patch.object(publish, 'run', side_effect=['', "package: name='com.xuper.netxxus' versionCode='43405' versionName='1.1'"]), \
                 self.assertRaises(ValueError):
                publish.inspect_apk(apk, '1.1')


if __name__ == '__main__':
    unittest.main()
