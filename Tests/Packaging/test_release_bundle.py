"""Offline fault injection; actual device archive remains a separate CI check."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from verify_release_bundle import validate_resources


class ReleaseResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.expected, self.app = self.root / 'expected', self.root / 'App'
        model = self.expected / 'Suxin'; model.mkdir(parents=True)
        files = []
        for name in ['model.onnx', 'config.json', 'lexicon.json', 'syllables.json', 'author-LICENSE.txt', 'pypinyin-LICENSE.txt']:
            data = ('original validator fixture ' + name).encode()
            (model / name).write_bytes(data)
            files.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        (model / 'manifest.json').write_text(json.dumps({'files': files}))
        notices = self.expected / 'NativeNotices'; notices.mkdir()
        rows = []
        for name in ['ONNXRuntime-LICENSE.txt', 'ONNXRuntime-ThirdPartyNotices.txt']:
            data = ('original notice validator fixture ' + name).encode()
            (notices / name).write_bytes(data)
            rows.append({'bundle_file': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        (notices / 'runtime-provenance.json').write_text(json.dumps({'supplemental_source_notices': rows}))
        (notices / 'Integration-NOTICE.md').write_text('original integration fixture')
        shutil.copytree(self.expected, self.app)

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_model_and_four_required_declarations_are_accepted(self):
        self.assertEqual(validate_resources(self.app, self.expected)['runtime_source_notice_files_verified'], 2)

    def test_missing_or_modified_declaration_is_rejected(self):
        (self.app / 'NativeNotices/ONNXRuntime-LICENSE.txt').write_bytes(b'corrupt')
        with self.assertRaises(ValueError): validate_resources(self.app, self.expected)

    def test_model_byte_change_is_rejected(self):
        (self.app / 'Suxin/model.onnx').write_bytes(b'bad model')
        with self.assertRaises(ValueError): validate_resources(self.app, self.expected)

    def test_unlisted_text_audio_books_and_keys_are_rejected(self):
        for name in ['private.txt', 'novel.epub', 'voice.wav', 'secret.p8']:
            with self.subTest(name=name):
                p = self.app / name; p.write_bytes(b'original forbidden fixture')
                with self.assertRaises(ValueError): validate_resources(self.app, self.expected)
                p.unlink()

    def test_unlisted_model_resource_is_rejected(self):
        (self.app / 'Suxin/extra.json').write_text('{}')
        with self.assertRaises(ValueError): validate_resources(self.app, self.expected)
