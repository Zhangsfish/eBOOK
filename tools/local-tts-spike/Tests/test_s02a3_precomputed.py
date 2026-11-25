"""Provenance guards using actual author-exported IDs; no speech mocks."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / 's02a3/scripts'))
from validate_precomputed import validate_precomputed


class AuthorIDGuards(unittest.TestCase):
    def setUp(self):
        self.path = SPIKE / 's02a3/fixtures/suxin-author-ids.json'
        self.pins = json.loads((SPIKE / 's02a3/manifests/precomputed-ids.json').read_text(encoding='utf-8'))

    def check_mutation(self, mutate, update_pin=False):
        value = json.loads(self.path.read_text(encoding='utf-8'))
        mutate(value)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'ids.json'; pins = Path(folder) / 'pins.json'
            raw = json.dumps(value).encode(); path.write_bytes(raw)
            if update_pin:
                self.pins['prepared_ids_sha256'] = hashlib.sha256(raw).hexdigest()
            pins.write_text(json.dumps(self.pins), encoding='utf-8')
            with self.assertRaises(ValueError):
                validate_precomputed(path, pins)

    def test_actual_pinned_export_retains_backend_only_boundary(self):
        result = validate_precomputed(self.path)
        self.assertEqual(result['validated_cases'], 5)
        self.assertFalse(result['end_to_end_native_text'])

    def test_changed_ids_fail_the_recorded_author_export_digest(self):
        self.check_mutation(lambda v: v['records'][0]['ids'].pop())

    def test_native_text_claim_is_rejected_even_with_updated_file_digest(self):
        self.check_mutation(lambda v: v.update(end_to_end_native_text=True), True)

    def test_substituted_original_text_hash_is_rejected(self):
        self.check_mutation(lambda v: v['records'][0].update(text_sha256='0' * 64), True)

    def test_unbounded_or_boolean_tensor_ids_are_rejected(self):
        self.check_mutation(lambda v: v['records'][0].update(ids=[True] * 2050), True)


if __name__ == '__main__':
    unittest.main()
