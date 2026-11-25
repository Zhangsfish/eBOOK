"""Exercise the downloaded artifact privacy boundary, never speech inference."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 's02a2/scripts'))
from verify_ci_artifact import inspect


class DownloadedArtifactGuard(unittest.TestCase):
    def archive(self, directory, name, content):
        path = Path(directory) / 'metadata.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(name, json.dumps(content))
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_modified_zip_cannot_be_trusted(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = self.archive(directory, 'native-result-0.json', {'source_sha': 'expected'})
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                inspect(path, '0' * 64, 'expected')

    def test_path_traversal_is_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path, digest = self.archive(directory, '../native-result-0.json', {})
            with self.assertRaisesRegex(ValueError, 'selected JSON|small selected JSON'):
                inspect(path, digest, 'expected')

    def test_disguised_audio_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path, digest = self.archive(directory, 'native-result-0.json', {'pcm': [0, 1]})
            with self.assertRaisesRegex(ValueError, 'payload prohibited'):
                inspect(path, digest, 'expected')


if __name__ == '__main__': unittest.main()
