"""Metadata/security guards only; no simulated speech inference."""
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 's02a2/scripts'))
from model_assets import SPIKE
from run_native import parse_metric, coreml_execution
from publish_native import reject_media_payload


class CandidateGuards(unittest.TestCase):
    def value(self):
        corpus = json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases']
        return {'kind': 'matcha', 'environment': 'IOS_SIMULATOR', 'run_context': {'source_sha': 'tested-sha'},
                'genuine_ios_inference': True,
                'records': [{'fixture_id': c['id'], 'sample_rate': 22050, 'frames': 44100,
                    'duration_seconds': 2, 'generation_seconds': 1, 'rtf': .5, 'rms': .1,
                    'wav_sha256': 'a' * 64, 'process_peak_rss_cumulative_bytes': 1024} for c in corpus]}

    def parse(self, value, kind='matcha'):
        return parse_metric('S02A2_METRICS ' + json.dumps(value), 'tested-sha', kind)

    def test_provider_listing_is_not_execution(self):
        self.assertEqual(coreml_execution({'available_providers': ['CoreMLExecutionProvider']}), 'NOT_PROVEN_NODE_ASSIGNMENT')

    def test_cpu_profile_is_not_coreml(self):
        self.assertEqual(coreml_execution({'status': 'ACTUAL_ORT_PROFILE_INSPECTED',
            'provider_node_event_counts': {'CPUExecutionProvider': 200}}), 'CPU_FALLBACK_NO_COREML_NODE_EVENTS')

    def test_real_coreml_profile_still_does_not_claim_ane(self):
        self.assertEqual(coreml_execution({'status': 'ACTUAL_ORT_PROFILE_INSPECTED',
            'provider_node_event_counts': {'CoreMLExecutionProvider': 1}}), 'COREML_NODE_EVENTS_OBSERVED_ANE_NOT_MEASURED')

    def test_native_parser_rejects_desktop(self):
        value = self.value(); value['environment'] = 'DESKTOP_CPU'
        with self.assertRaises(ValueError): self.parse(value)

    def test_native_parser_rejects_missing_original_case(self):
        value = self.value(); value['records'].pop()
        with self.assertRaises(ValueError): self.parse(value)

    def test_native_parser_rejects_inconsistent_duration(self):
        value = self.value(); value['records'][0]['duration_seconds'] = 3
        with self.assertRaises(ValueError): self.parse(value)

    def test_backend_cannot_claim_complete_native_frontend(self):
        value = self.value(); value.update(kind='suxin_backend', genuine_ios_graph_inference=True,
            end_to_end_native_text=True, frontend_mode='AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS')
        with self.assertRaises(ValueError): self.parse(value, 'suxin_backend')

    def test_valid_backend_keeps_frontend_limitation(self):
        value = self.value(); value.update(kind='suxin_backend', genuine_ios_graph_inference=True,
            end_to_end_native_text=False, frontend_mode='AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS')
        self.assertFalse(self.parse(value, 'suxin_backend')['end_to_end_native_text'])

    def test_raw_audio_or_text_cannot_enter_public_metrics(self):
        for field in ['samples', 'pcm', 'waveform', 'text', 'private_key']:
            with self.subTest(field=field), self.assertRaises(ValueError):
                reject_media_payload({'records': [{field: 'test fixture, not private data'}]})

    def test_metadata_hashes_and_counts_are_allowed(self):
        reject_media_payload({'records': [{'text_sha256': 'a' * 64, 'frames': 44100, 'wav_sha256': 'b' * 64}]})


if __name__ == '__main__': unittest.main()
