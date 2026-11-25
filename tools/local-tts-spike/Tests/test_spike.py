from pathlib import Path
import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest

SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / 'scripts'))
from assets import REPO, safe_relative, sha256, verify, extract_verified
from run_desktop import validate_request


class AssetIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.parent = REPO / '.local-test-data/s02a/test-tmp'
        self.parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.parent)
        self.root = Path(self.temp.name).resolve()
        self.assertTrue(self.root.is_relative_to(self.parent.resolve()))

    def tearDown(self):
        self.temp.cleanup()  # Only this test's newly created directory.

    def manifest(self, payload=b'original fixture'):
        return {'directory': 'kokoro', 'unpacked_bytes': len(payload), 'files': [
            {'path': 'data.txt', 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}]}

    def archive(self, entries, manifest):
        archive = self.root / 'model.tar.bz2'
        with tarfile.open(archive, 'w:bz2') as target:
            for name, payload, link in entries:
                item = tarfile.TarInfo(name)
                if link:
                    item.type = tarfile.SYMTYPE; item.linkname = '/outside'
                    target.addfile(item)
                else:
                    item.size = len(payload); target.addfile(item, io.BytesIO(payload))
        manifest['archive'] = {'sha256': sha256(archive), 'bytes': archive.stat().st_size}
        return archive

    def test_verifies_exact_file_set(self):
        model = self.root / 'model'; model.mkdir(); (model / 'data.txt').write_bytes(b'original fixture')
        self.assertEqual(verify(model, self.manifest())['status'], 'PASS')

    def test_corruption_rejected(self):
        model = self.root / 'model'; model.mkdir(); (model / 'data.txt').write_bytes(b'changed fixture!')
        with self.assertRaises(ValueError): verify(model, self.manifest())

    def test_unexpected_file_rejected(self):
        (self.root / 'data.txt').write_bytes(b'original fixture'); (self.root / 'extra').touch()
        with self.assertRaises(ValueError): verify(self.root, self.manifest())

    def test_missing_file_rejected(self):
        with self.assertRaises(ValueError): verify(self.root, self.manifest())

    def test_traversal_and_windows_paths_rejected(self):
        for name in ['../outside', '/outside', 'C:/outside', 'a\\outside', 'a/../../outside']:
            with self.subTest(name=name), self.assertRaises(ValueError): safe_relative(name)

    def test_safe_archive_extracts_and_verifies(self):
        manifest = self.manifest(); archive = self.archive([('kokoro/data.txt', b'original fixture', False)], manifest)
        self.assertEqual(extract_verified(archive, self.root / 'new', manifest)['status'], 'PASS')

    def test_existing_destination_is_preserved(self):
        manifest = self.manifest(); archive = self.archive([('kokoro/data.txt', b'original fixture', False)], manifest)
        target = self.root / 'existing'; target.mkdir(); (target / 'owner.txt').write_text('preserve')
        with self.assertRaises(FileExistsError): extract_verified(archive, target, manifest)
        self.assertEqual((target / 'owner.txt').read_text(), 'preserve')

    def test_archive_checksum_failure_preserves_destination_absence(self):
        manifest = self.manifest(); archive = self.archive([('kokoro/data.txt', b'original fixture', False)], manifest)
        manifest['archive']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): extract_verified(archive, self.root / 'new', manifest)
        self.assertFalse((self.root / 'new').exists())

    def test_archive_symlink_rejected(self):
        manifest = self.manifest(); archive = self.archive([
            ('kokoro/data.txt', b'original fixture', False), ('kokoro/link', b'', True)], manifest)
        with self.assertRaises(ValueError): extract_verified(archive, self.root / 'new', manifest)

    def test_archive_traversal_rejected(self):
        manifest = self.manifest(); archive = self.archive([('kokoro/../data.txt', b'original fixture', False)], manifest)
        with self.assertRaises(ValueError): extract_verified(archive, self.root / 'new', manifest)

    def test_duplicate_archive_member_rejected(self):
        manifest = self.manifest(b'xx'); archive = self.archive([
            ('kokoro/data.txt', b'x', False), ('kokoro/data.txt', b'x', False)], manifest)
        with self.assertRaises(ValueError): extract_verified(archive, self.root / 'new', manifest)


class CorpusAndBoundsTests(unittest.TestCase):
    def test_original_corpus_covers_requested_categories(self):
        corpus = json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))
        self.assertEqual({r['id'] for r in corpus['cases']}, {'narration', 'dialogue', 'numbers', 'polyphones', 'mixed'})
        for item in corpus['cases']: validate_request(item['text'], 1.0)

    def test_oversized_and_empty_inputs_rejected(self):
        for text in ['', '  ', '字' * 241]:
            with self.subTest(text_length=len(text)), self.assertRaises(ValueError): validate_request(text, 1.0)

    def test_invalid_rates_rejected(self):
        for rate in [0, -1, 2.1, float('nan'), float('inf')]:
            with self.subTest(rate=rate), self.assertRaises(ValueError): validate_request('原创测试', rate)

    def test_manifest_footprint_is_complete(self):
        manifest = json.loads((SPIKE / 'manifests/model.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['files']), 377)
        self.assertEqual(sum(r['bytes'] for r in manifest['files']), manifest['unpacked_bytes'])
        self.assertEqual(len({r['path'] for r in manifest['files']}), 377)


if __name__ == '__main__': unittest.main()
