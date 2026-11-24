from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from assets import REPO
from inspect_native import inspect_archive
from publish_evidence import sanitize
from run_matrix import parse_native_metrics


class NativeMetricGuards(unittest.TestCase):
    def value(self):
        # Synthetic METADATA for parser tests only. No mock audio/model execution.
        rows = [{'speaker_id': sid, 'sample_rate': 24000, 'frames': 48000, 'duration_seconds': 2,
                 'rms': .1, 'rtf': .5, 'generation_seconds': 1, 'first_callback_seconds': .2,
                 'process_peak_rss_cumulative_bytes': 1000, 'wav_sha256': ('%064x' % (index + 1))}
                for index, sid in enumerate([3, 4, 58, 3, 3, 3, 3])]
        return {'kind': 'thread_benchmark', 'environment': 'IOS_SIMULATOR', 'genuine_ios_inference': True,
                'run_context': {'source_sha': 'tested-sha'}, 'threads': 1, 'records': rows}

    def parse(self, value, prefix=''):
        return parse_native_metrics(prefix + 'S02A_IOS_METRICS ' + json.dumps(value), 'thread_benchmark', 'tested-sha', 1)

    def test_actual_marker_statistics(self):
        self.assertEqual(self.parse(self.value())['statistics']['p95_rtf_nearest_rank'], .5)

    def test_compile_only_output_rejected(self):
        with self.assertRaises(ValueError): parse_native_metrics('BUILD SUCCEEDED', 'thread_benchmark', 'tested-sha', 1)

    def test_desktop_marker_rejected(self):
        value = self.value(); value['environment'] = 'MACOS_DESKTOP_NOT_IOS'
        with self.assertRaises(ValueError): self.parse(value)

    def test_false_native_flag_rejected(self):
        value = self.value(); value['genuine_ios_inference'] = False
        with self.assertRaises(ValueError): self.parse(value)

    def test_wrong_sha_rejected(self):
        value = self.value(); value['run_context']['source_sha'] = 'other-sha'
        with self.assertRaises(ValueError): self.parse(value)

    def test_wrong_threads_rejected(self):
        value = self.value(); value['threads'] = 4
        with self.assertRaises(ValueError): self.parse(value)

    def test_missing_case_rejected(self):
        value = self.value(); value['records'].pop()
        with self.assertRaises(ValueError): self.parse(value)

    def test_inconsistent_audio_duration_rejected(self):
        value = self.value(); value['records'][0]['duration_seconds'] = 3
        with self.assertRaises(ValueError): self.parse(value)

    def test_inconsistent_rtf_rejected(self):
        value = self.value(); value['records'][0]['rtf'] = .1
        with self.assertRaises(ValueError): self.parse(value)

    def test_missing_hash_rejected(self):
        value = self.value(); del value['records'][0]['wav_sha256']
        with self.assertRaises(ValueError): self.parse(value)

    def test_ambiguous_duplicate_marker_rejected(self):
        marker = 'S02A_IOS_METRICS ' + json.dumps(self.value())
        with self.assertRaises(ValueError): parse_native_metrics(marker + '\n' + marker, 'thread_benchmark', 'tested-sha', 1)

    def equivalence(self):
        return {'kind': 'minimal_equivalence', 'environment': 'IOS_SIMULATOR',
                'genuine_ios_inference': True, 'run_context': {'source_sha': 'tested-sha'},
                'original_cases': 7, 'full_frames': [48000] * 7, 'minimal_frames': [48000] * 7,
                'full_wav_sha256': ['a' * 64] * 7, 'minimal_wav_sha256': ['a' * 64] * 7,
                'bit_identical_pcm16_wav': True}

    def parse_equivalence(self, value):
        return parse_native_metrics('S02A_IOS_METRICS ' + json.dumps(value),
                                    'minimal_equivalence', 'tested-sha')

    def test_equivalence_cannot_claim_pass_with_different_waveforms(self):
        value = self.equivalence(); value['minimal_wav_sha256'][0] = 'b' * 64
        with self.assertRaises(ValueError): self.parse_equivalence(value)

    def test_equivalence_requires_actual_hashes(self):
        value = self.equivalence(); value['full_wav_sha256'][0] = 'BUILD SUCCEEDED'
        with self.assertRaises(ValueError): self.parse_equivalence(value)

    def test_equivalence_failure_preserves_actual_comparison(self):
        value = self.equivalence(); value['minimal_frames'][0] = 96000
        value['bit_identical_pcm16_wav'] = False
        result = self.parse_equivalence(value)
        self.assertFalse(result['bit_identical_pcm16_wav'])
        self.assertEqual(result['minimal_frames'][0], 96000)


class ArchiveAndRedactionGuards(unittest.TestCase):
    def setUp(self):
        parent = REPO / '.local-test-data/s02a1/unit-tmp'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name).resolve()
        self.assertTrue(self.root.is_relative_to(parent.resolve()))

    def tearDown(self): self.temp.cleanup()

    def test_native_archive_missing_info_fails(self):
        path = self.root / 'empty.zip'
        with zipfile.ZipFile(path, 'w') as target: target.writestr('README', 'public fixture')
        with self.assertRaises(ValueError): inspect_archive(path, self.root)

    def test_native_archive_path_traversal_fails(self):
        path = self.root / 'unsafe.zip'
        with zipfile.ZipFile(path, 'w') as target: target.writestr('../outside', 'public fixture')
        with self.assertRaises(ValueError): inspect_archive(path, self.root)

    def test_redaction_removes_potential_token_and_native_text_diagnostics(self):
        text = 'Bearer ' + 'TESTONLY123\nTokenizeFromLexiconStr: text=original fixture\nsafe metric'
        clean = sanitize(text)
        self.assertNotIn('TESTONLY123', clean)
        self.assertNotIn('text=', clean)
        self.assertIn('safe metric', clean)


if __name__ == '__main__': unittest.main()
