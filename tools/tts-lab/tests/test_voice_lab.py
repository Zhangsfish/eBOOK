"""All tests are offline. Generated files stay inside the ignored audition root."""
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import os
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import wave
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run import main
from tts_lab.adapters import ADAPTERS
from tts_lab.adapters.azure import MSTTS, SSML
from tts_lab.billing import CostEstimate, azure_billable_units, check_spend_cap, estimate
from tts_lab.core import (AudioSpec, HTTPResponse, LabError, MAX_RESPONSE_BYTES,
                          SynthesisRequest, chunks, join_wavs, normalize_text, text_counts,
                          validate_wav, wav_from_pcm)
from tts_lab.corpus import load_samples
from tts_lab.lab import anonymous_label, conditions, read_voice_configuration, run_lab
from tts_lab.player import write_player
from tts_lab.ratings import CRITERIA, weighted_score
from tts_lab.storage import AudioCache, OUTPUT_ROOT, REPOSITORY, safe_output_directory
from tts_lab.transport import GuardedHTTPTransport, LivePolicy, MockTransport, mock_wav

NETWORK_PATCHES = []


def setUpModule():
    for target in ('socket.socket', 'socket.getaddrinfo', 'socket.create_connection',
                   'urllib.request.OpenerDirector.open'):
        guard = patch(target, side_effect=AssertionError('Network is forbidden in S01 tests.'))
        guard.start(); NETWORK_PATCHES.append(guard)


def tearDownModule():
    for guard in reversed(NETWORK_PATCHES):
        guard.stop()


def request(provider, model=None, style='neutral', text='中文测试。A与𠮷。'):
    voices = {'minimax': 'Chinese (Mandarin)_Lyrical_Voice', 'fish': '0' * 32,
              'elevenlabs': 'OZ0L6eISlOejga3XjDFt', 'azure': 'zh-CN-XiaoxiaoNeural'}
    return SynthesisRequest(provider, model or ADAPTERS[provider].models[0], voices[provider],
                            text, style, region='eastus' if provider == 'azure' else None)


class TextAndBillingTests(unittest.TestCase):
    def test_original_suite_counts_and_required_categories(self):
        samples = load_samples()
        self.assertEqual([s.id for s in samples], ['narration', 'dialogue', 'restraint', 'numbers', 'boundaries', 'names'])
        self.assertEqual(sum(len(s.text) for s in samples), 930)
        self.assertEqual(sum(text_counts(s.text)['utf8_bytes'] for s in samples), 2643)
        self.assertEqual(sum(text_counts(s.text)['utf16_units'] for s in samples), 931)
        self.assertEqual(sum(len(s.pieces) for s in samples), 12)
        self.assertGreater(len(samples[4].pieces), 1)
        self.assertTrue(samples[5].pronunciation_notes)

    def test_unicode_accounting_is_not_interchangeable(self):
        self.assertEqual(text_counts('中A𠀀😀'), {'unicode_scalars': 4, 'utf8_bytes': 12, 'utf16_units': 6})

    def test_normalization_and_lossless_shared_chunk_boundaries(self):
        text = 'e\u0301\r\n她说：“慢一点。”\r\n\r\n' + '一个没有标点的连续长句😀' * 40
        normalized = normalize_text(text)
        self.assertTrue(normalized.startswith('é\n'))
        result = chunks(text)
        self.assertEqual(''.join(result), normalized)
        self.assertTrue(all(len(part) <= 120 and part.strip() for part in result))
        for sample in load_samples():
            self.assertEqual(''.join(sample.pieces), sample.text)

    def test_invalid_text_and_chunk_sizes_are_rejected(self):
        for text in ('', '   ', '\ud800', '中\x00文'):
            with self.subTest(text=repr(text)), self.assertRaises(LabError):
                normalize_text(text)
        for limit in (0, 7, 121, 10000):
            with self.assertRaises(LabError):
                chunks('正文。', maximum=limit)

    def test_minimax_and_eleven_dated_character_estimates(self):
        for provider, model, price in [('minimax', 'speech-2.8-hd', '100'),
                                       ('minimax', 'speech-2.8-turbo', '60'),
                                       ('elevenlabs', 'eleven_v4', '80'),
                                       ('elevenlabs', 'eleven_multilingual_v2', '80')]:
            with self.subTest(provider=provider, model=model):
                req = request(provider, model, text='中A𠀀')
                cost = estimate(req, ADAPTERS[provider].prepare(req))
                self.assertEqual(cost.units, 3)
                self.assertEqual(cost.usd, Decimal(price) * 3 / 1_000_000)

    def test_fish_prices_utf8_bytes_and_free_is_not_unknown(self):
        req = request('fish', text='中A𠀀')
        cost = estimate(req, ADAPTERS['fish'].prepare(req))
        self.assertEqual(cost.units, 8)
        self.assertEqual(cost.usd, Decimal('0.000120'))
        free = replace(req, model='s2.1-pro-free')
        self.assertEqual(estimate(free, ADAPTERS['fish'].prepare(free)).usd, Decimal(0))
        azure = request('azure', text='中A𠀀')
        self.assertIsNone(estimate(azure, ADAPTERS['azure'].prepare(azure)).usd)

    def test_azure_doubles_han_and_counts_inner_ssml_markup(self):
        req = request('azure', text='中A𠀀')
        self.assertEqual(azure_billable_units(ADAPTERS['azure'].prepare(req)), 5)
        styled = replace(req, style='gentle')
        expected_inner = '<mstts:express-as style="gentle">中A𠀀</mstts:express-as>'
        self.assertEqual(azure_billable_units(ADAPTERS['azure'].prepare(styled)), len(expected_inner) + 2)

    def test_budget_refuses_unknown_excessive_or_invalid_caps(self):
        known = [CostEstimate(1000, 'characters', Decimal('100'), '')]
        self.assertEqual(check_spend_cap('0.1', known), Decimal('0.1'))
        for cap in ('0.09', '0', '-1', 'NaN', 'Infinity', 'not-a-number', None):
            with self.subTest(cap=cap), self.assertRaises(LabError):
                check_spend_cap(cap, known)
        with self.assertRaises(LabError):
            check_spend_cap('999', [CostEstimate(1, 'unknown', None, '')])

    def test_invalid_quotes_cannot_reduce_a_future_spend_guard(self):
        for units, price in [(-1, Decimal('10')), (1, Decimal('-1')), (1, Decimal('NaN')), (1, Decimal('Infinity'))]:
            with self.assertRaises(LabError):
                CostEstimate(units, 'invalid', price, '')

    def test_weighted_scores_require_all_seven_real_ratings(self):
        self.assertEqual(sum(weight for _, _, weight in CRITERIA), 100)
        self.assertIsNone(weighted_score({}))
        values = {name: 5 for name, _, _ in CRITERIA}
        self.assertEqual(weighted_score(values), Decimal(5))
        values['comfort'] = 1
        self.assertEqual(weighted_score(values), Decimal('3.8'))
        for value in (0, 6, 'NaN', 'Infinity', '2.5', 'bad'):
            with self.subTest(value=value), self.assertRaises(LabError):
                weighted_score({**values, 'naturalness': value})


class AdapterTests(unittest.TestCase):
    def test_minimax_explicit_model_hex_and_wav_contract(self):
        for model in ADAPTERS['minimax'].models:
            req = request('minimax', model, 'gentle')
            plan = ADAPTERS['minimax'].prepare(req)
            body = json.loads(plan.body)
            self.assertEqual(plan.url, 'https://api.minimax.io/v1/t2a_v2')
            self.assertEqual(body['model'], model)
            self.assertFalse(body['stream']); self.assertEqual(body['output_format'], 'hex')
            self.assertEqual(body['voice_setting']['emotion'], 'calm')
            self.assertEqual(body['audio_setting'], {'sample_rate': 24000, 'format': 'wav', 'channel': 1})
            self.assertEqual(body['text'], req.text)
            self.assertNotIn('voice_modify', body)
            self.assertEqual(plan.auth.environment, 'MINIMAX_API_KEY')

    def test_fish_model_header_json_and_no_cloning(self):
        for model in ADAPTERS['fish'].models:
            req = request('fish', model)
            plan = ADAPTERS['fish'].prepare(req)
            body = json.loads(plan.body)
            self.assertEqual(plan.headers['model'], model)
            self.assertEqual(plan.url, 'https://api.fish.audio/v1/tts')
            self.assertEqual(body['reference_id'], '0' * 32)
            self.assertNotIn('references', body)
            self.assertNotIn('language', body)
            self.assertEqual((body['format'], body['sample_rate']), ('wav', 24000))
            self.assertFalse(body['prosody']['normalize_loudness'])
            self.assertEqual(body['text'], req.text)

    def test_eleven_v4_and_multilingual_v2_do_not_share_unsupported_language_field(self):
        for model in ADAPTERS['elevenlabs'].models:
            req = request('elevenlabs', model)
            plan = ADAPTERS['elevenlabs'].prepare(req)
            body = json.loads(plan.body)
            self.assertTrue(plan.url.endswith('?output_format=wav_24000'))
            self.assertEqual(body['model_id'], model)
            self.assertEqual(body['voice_settings'], {'speed': 1.0})
            self.assertEqual('language_code' in body, model == 'eleven_v4')
            self.assertNotIn('enable_logging', plan.url)
            self.assertEqual(plan.auth.header, 'xi-api-key')

    def test_azure_neural_ssml_style_rate_and_text_escaping(self):
        req = replace(request('azure', style='gentle', text='中<&>A'), rate=0.9)
        plan = ADAPTERS['azure'].prepare(req)
        xml = ET.fromstring(plan.body)
        self.assertEqual(''.join(xml.itertext()), req.text)
        self.assertEqual(xml.find(f'.//{{{MSTTS}}}express-as').attrib['style'], 'gentle')
        self.assertEqual(xml.find(f'.//{{{SSML}}}prosody').attrib['rate'], '-10.0000%')
        self.assertEqual(plan.headers['X-Microsoft-OutputFormat'], 'riff-24khz-16bit-mono-pcm')
        self.assertEqual(plan.url, 'https://eastus.tts.speech.microsoft.com/cognitiveservices/v1')

    def test_azure_hd_uses_documented_voice_family_and_no_unsupported_prosody(self):
        req = replace(request('azure'), model='dragon-hd-flash', voice='zh-CN-Xiaoyi:DragonHDFlashLatestNeural')
        xml = ET.fromstring(ADAPTERS['azure'].prepare(req).body)
        self.assertIsNone(xml.find(f'.//{{{SSML}}}prosody'))
        with self.assertRaises(LabError):
            ADAPTERS['azure'].prepare(replace(req, rate=0.9))
        with self.assertRaises(LabError):
            ADAPTERS['azure'].prepare(replace(req, voice='zh-CN-XiaoxiaoNeural'))

    def test_unsupported_styles_models_bad_voice_ids_and_regions_fail_explicitly(self):
        for provider in ('fish', 'elevenlabs'):
            with self.subTest(provider=provider), self.assertRaises(LabError):
                ADAPTERS[provider].prepare(request(provider, style='gentle'))
        for provider in ADAPTERS:
            with self.subTest(provider=provider), self.assertRaises(LabError):
                ADAPTERS[provider].prepare(replace(request(provider), model='unreviewed'))
        for req in [replace(request('fish'), voice=''), replace(request('elevenlabs'), voice='../escape'),
                    replace(request('azure'), region='evil.example/'), replace(request('minimax'), rate=float('nan')),
                    replace(request('minimax'), audio=AudioSpec(sample_rate=44100))]:
            with self.assertRaises(LabError):
                ADAPTERS[req.provider].prepare(req)

    def test_all_adapters_decode_mock_completed_audio_without_credentials(self):
        for provider, adapter in ADAPTERS.items():
            for model in adapter.models:
                req = request(provider, model)
                if provider == 'azure' and model == 'dragon-hd-flash':
                    req = replace(req, voice='zh-CN-Xiaoyi:DragonHDFlashLatestNeural')
                transport = MockTransport()
                result = adapter.synthesize(req, transport)
                self.assertEqual(result, mock_wav())
                self.assertEqual(len(transport.calls), 1)
                self.assertNotIn('Authorization', transport.calls[0].headers)

    def test_http_errors_are_sanitized_and_never_retried(self):
        for provider, adapter in ADAPTERS.items():
            for status in (400, 401, 402, 403, 404, 415, 429, 500, 503):
                transport = MockTransport([HTTPResponse(status, b'SENTINEL_SHOULD_NOT_LEAK')])
                with self.subTest(provider=provider, status=status), self.assertRaises(LabError) as failure:
                    adapter.synthesize(request(provider), transport)
                self.assertNotIn('SENTINEL', str(failure.exception))
                self.assertEqual(len(transport.calls), 1)

    def test_minimax_application_errors_null_stream_url_and_hex_validation(self):
        adapter = ADAPTERS['minimax']
        values = [{'base_resp': {'status_code': code}, 'data': None}
                  for code in (1000, 1001, 1002, 1004, 2013, 0)]
        values += [{'base_resp': {'status_code': 0}, 'data': {'status': status, 'audio': audio}}
                   for status, audio in ((1, mock_wav().hex()), (2, 'https://not-followed.invalid/audio'), (2, 'bad hex'))]
        values += [None, [], {'base_resp': 'invalid'}, {'data': {'audio': '00'}}, {'base_resp': {'status_code': False}}]
        for value in values:
            response = HTTPResponse(200, json.dumps(value).encode())
            with self.subTest(value_type=type(value).__name__), self.assertRaises(LabError):
                adapter.parse(response, request('minimax'))

    def test_invalid_truncated_wrong_format_and_oversized_audio_are_not_cached(self):
        for data in (b'', b'not WAV', mock_wav()[:-20], b'0' * (MAX_RESPONSE_BYTES + 1)):
            with self.assertRaises(LabError):
                ADAPTERS['fish'].parse(HTTPResponse(200, data), request('fish'))
        output = BytesIO()
        with wave.open(output, 'wb') as stream:
            stream.setnchannels(2); stream.setsampwidth(2); stream.setframerate(44100); stream.writeframes(b'\x00' * 20)
        with self.assertRaises(LabError):
            validate_wav(output.getvalue())

    def test_identical_normalized_text_reaches_every_provider(self):
        text = normalize_text('她说：\r\n“等等……A与𠮷。”')
        for provider, adapter in ADAPTERS.items():
            plan = adapter.prepare(request(provider, text=text))
            actual = ''.join(ET.fromstring(plan.body).itertext()) if provider == 'azure' else json.loads(plan.body)['text']
            self.assertEqual(actual, text)

    def test_wav_join_preserves_frames_and_does_not_insert_gaps(self):
        self.assertEqual(validate_wav(join_wavs([mock_wav(), mock_wav()])), validate_wav(mock_wav()) * 2)


class LocalWorkflowTests(unittest.TestCase):
    def setUp(self):
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='unittest-', dir=OUTPUT_ROOT)
        self.directory = Path(self.temporary.name).resolve()
        self.assertTrue(self.directory.is_relative_to(OUTPUT_ROOT.resolve()))

    def tearDown(self):
        self.assertTrue(Path(self.temporary.name).resolve().is_relative_to(OUTPUT_ROOT.resolve()))
        self.temporary.cleanup()

    def test_cache_reuses_audio_without_second_transport_attempt(self):
        cache, transport, req = AudioCache(self.directory / 'cache'), MockTransport(), request('minimax')
        first, hit = cache.get_or_synthesize(ADAPTERS['minimax'], req, transport)
        second, hit_again = cache.get_or_synthesize(ADAPTERS['minimax'], req, transport)
        self.assertFalse(hit); self.assertTrue(hit_again)
        self.assertEqual(first, second); self.assertEqual(len(transport.calls), 1)
        record = next((self.directory / 'cache').rglob('record.json')).read_text(encoding='utf-8')
        self.assertNotIn(req.text, record)

    def test_cache_identity_covers_model_voice_text_style_rate_region_format_and_provenance(self):
        req = request('minimax')
        variations = [replace(req, provider='fish'), replace(req, model='speech-2.8-turbo'), replace(req, voice='another_voice'),
                      replace(req, text='不同文本'), replace(req, style='gentle'), replace(req, rate=0.9),
                      replace(req, region='another-region'), replace(req, audio=AudioSpec(sample_rate=44100))]
        keys = {req.cache_key('mock'), req.cache_key('live'), *[item.cache_key('mock') for item in variations]}
        self.assertEqual(len(keys), 10)

    def test_corrupt_cache_never_silently_rebills(self):
        cache, transport, req = AudioCache(self.directory / 'cache'), MockTransport(), request('fish')
        cache.get_or_synthesize(ADAPTERS['fish'], req, transport)
        next((self.directory / 'cache').rglob('audio.wav')).write_bytes(b'corrupt')
        with self.assertRaises(LabError):
            cache.get_or_synthesize(ADAPTERS['fish'], req, transport)
        self.assertEqual(len(transport.calls), 1)

    def test_ambiguous_timeout_remains_blocked_on_rerun(self):
        cache, req = AudioCache(self.directory / 'cache'), request('elevenlabs')
        transport = MockTransport([TimeoutError('SENTINEL_SHOULD_NOT_LEAK')])
        for _ in range(2):
            with self.assertRaises(LabError) as failure:
                cache.get_or_synthesize(ADAPTERS['elevenlabs'], req, transport)
            self.assertNotIn('SENTINEL', str(failure.exception))
        self.assertEqual(len(transport.calls), 1)
        record = json.loads(next((self.directory / 'cache').rglob('record.json')).read_text(encoding='utf-8'))
        self.assertEqual(record['state'], 'failed_or_ambiguous')

    def test_pending_claim_prevents_concurrent_duplicate_synthesis(self):
        entered, release = threading.Event(), threading.Event()
        class SlowMock(MockTransport):
            def send(self, plan):
                entered.set(); release.wait(3)
                return super().send(plan)
        cache, transport, req = AudioCache(self.directory / 'cache'), SlowMock(), request('fish')
        with ThreadPoolExecutor(max_workers=1) as executor:
            first = executor.submit(cache.get_or_synthesize, ADAPTERS['fish'], req, transport)
            self.assertTrue(entered.wait(3))
            try:
                with self.assertRaises(LabError):
                    cache.get_or_synthesize(ADAPTERS['fish'], req, transport)
            finally:
                release.set()
            first.result(timeout=3)
        self.assertEqual(len(transport.calls), 1)

    def test_output_and_configuration_cannot_escape_ignored_root(self):
        self.assertEqual(safe_output_directory(self.directory), self.directory)
        for path in (REPOSITORY, OUTPUT_ROOT / '..' / 'outside', Path('outside-output')):
            with self.assertRaises(LabError):
                safe_output_directory(path)
        config = self.directory / 'voices.json'
        config.write_text(json.dumps({'minimax/speech-2.8-hd/female': 'chosen_existing_voice'}), encoding='utf-8')
        self.assertEqual(read_voice_configuration(config)['minimax/speech-2.8-hd/female'], 'chosen_existing_voice')
        config.write_text('{"MINIMAX_API_KEY":"SENTINEL_SHOULD_NOT_LEAK"}', encoding='utf-8')
        with self.assertRaises(LabError) as failure:
            read_voice_configuration(config)
        self.assertNotIn('SENTINEL', str(failure.exception))

    def test_default_cli_is_dry_run_and_does_not_read_provider_credentials(self):
        original_get = os.environ.get
        secret_names = {'MINIMAX_API_KEY', 'FISH_API_KEY', 'ELEVENLABS_API_KEY', 'AZURE_SPEECH_KEY'}
        def guarded_get(name, *args):
            if name in secret_names:
                raise AssertionError('Dry run attempted to read a credential.')
            return original_get(name, *args)
        output = StringIO()
        with patch.object(os.environ, 'get', side_effect=guarded_get), redirect_stdout(output):
            code = main(['--provider', 'all', '--output', str(self.directory), '--seed', '31'])
        self.assertEqual(code, 0)
        result = json.loads(next(self.directory.glob('*dry_run*/session.json')).read_text(encoding='utf-8'))
        self.assertEqual((result['mode'], result['actual_vendor_requests'], result['incurred_cost_usd']), ('dry_run', 0, '0'))
        self.assertEqual(result['planned_chunk_requests'], 288)
        self.assertFalse(list(self.directory.rglob('*.wav')))

    def test_live_cli_remains_locked_even_with_flags_cap_and_environment_values(self):
        for cap in (None, '0', 'NaN', '100'):
            args = ['--execute-live', '--provider', 'minimax', '--output', str(self.directory)]
            if cap is not None:
                args += ['--max-spend-usd', cap]
            error = StringIO()
            with patch.dict(os.environ, {'MINIMAX_API_KEY': 'SENTINEL_SHOULD_NOT_LEAK'}), redirect_stderr(error):
                self.assertEqual(main(args), 2)
            self.assertNotIn('SENTINEL', error.getvalue())
        self.assertFalse(list(self.directory.iterdir()))

    def test_unauthorized_live_transport_fails_before_environment_or_socket_access(self):
        plan = ADAPTERS['fish'].prepare(request('fish'))
        transport = GuardedHTTPTransport(LivePolicy(True, '1', False), [])
        with patch.object(os.environ, 'get', side_effect=AssertionError('Credential read before authorization.')):
            with self.assertRaisesRegex(LabError, 'S01 forbids'):
                transport.send(plan)

    def test_future_transport_uses_ephemeral_auth_and_only_one_attempt_with_fake_opener(self):
        class FakeResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return mock_wav()
        class FakeOpener:
            def __init__(self): self.requests = []
            def open(self, wire, timeout): self.requests.append(wire); return FakeResponse()
        opener = FakeOpener()
        plan = ADAPTERS['fish'].prepare(request('fish'))
        transport = GuardedHTTPTransport(LivePolicy(True, '1', True),
                                         [(plan, estimate(request('fish'), plan))], opener)
        with patch.dict(os.environ, {'FISH_API_KEY': 'SENTINEL_SHOULD_NOT_LEAK'}):
            response = transport.send(plan)
            with self.assertRaises(LabError): transport.send(plan)
        self.assertEqual(response.body, mock_wav())
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(opener.requests[0].get_header('Authorization'), 'Bearer SENTINEL_SHOULD_NOT_LEAK')
        self.assertNotIn('SENTINEL', repr(plan))

    def test_future_transport_rejects_unreviewed_endpoint_before_credential_access(self):
        plan = replace(ADAPTERS['fish'].prepare(request('fish')), url='https://unreviewed.invalid/v1/tts')
        transport = GuardedHTTPTransport(LivePolicy(True, '1', True),
                                         [(plan, estimate(request('fish'), plan))])
        with patch.object(os.environ, 'get', side_effect=AssertionError('Must reject host first.')):
            with self.assertRaises(LabError): transport.send(plan)

    def test_future_transport_refuses_missing_or_changed_request_quotes(self):
        req = request('fish')
        plan = ADAPTERS['fish'].prepare(req)
        quote = estimate(req, plan)
        for approved in ([], [(replace(plan, body=b'different request'), quote)]):
            transport = GuardedHTTPTransport(LivePolicy(True, '1', True), approved)
            with patch.object(os.environ, 'get', side_effect=AssertionError('Must bind quote before credential access.')):
                with self.assertRaises(LabError): transport.send(plan)

    def test_mock_workflow_cache_and_generated_page_never_claim_vendor_audio(self):
        first_dir, first, mapping = run_lab('all', 'mock', self.directory, seed=17)
        second_dir, second, _ = run_lab('all', 'mock', self.directory, seed=17)
        self.assertEqual(first['mock_transport_calls'], 288)
        self.assertEqual(second['mock_transport_calls'], 0)
        self.assertEqual(second['mock_cache_hits'], 288)
        self.assertEqual(first['incurred_cost_usd'], '0')
        self.assertEqual(len(list(first_dir.glob('audio/*.wav'))), 144)
        html = (first_dir / 'index.html').read_text(encoding='utf-8')
        self.assertIn('0.16 秒测试音', html)
        self.assertIn('connect-src \'none\'', html)
        for token in ('minimax', 'elevenlabs', 's2.1-pro', 'Xiaoxiao', 'api.fish.audio'):
            self.assertNotIn(token, html)
        sheet = (first_dir / 'ratings.csv').read_text(encoding='utf-8-sig').splitlines()
        self.assertEqual(len(sheet), 33)
        self.assertTrue(all(row.endswith(',' * 9) for row in sheet[1:]))
        self.assertFalse(first['real_audio_generated']); self.assertIsNone(first['provider_selected'])
        for row in mapping:
            for sample in row['samples']:
                if not row['style_supported']:
                    self.assertIsNone(sample['audio'])

    def test_blind_mapping_order_is_stable_within_session_and_reproducible_with_seed(self):
        one_dir, _, one = run_lab('minimax', output=self.directory, seed=1)
        _, _, two = run_lab('minimax', output=self.directory, seed=1)
        _, _, three = run_lab('minimax', output=self.directory, seed=2)
        self.assertEqual(one, two); self.assertNotEqual(one, three)
        self.assertEqual([anonymous_label(i) for i in (0, 25, 26, 31)], ['A', 'Z', 'AA', 'AF'])
        page = (one_dir / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('"seed"', page)
        self.assertNotIn('"voice"', page)

    def test_player_escapes_script_breakout_and_rejects_remote_audio(self):
        sample = replace(load_samples()[0], text='</script><script>evil()</script>')
        write_player(self.directory, [sample], [{'sample_id': sample.id, 'alias': 'A', 'audio': None}], ['A'], 'dry_run')
        page = (self.directory / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('</script><script>evil()', page)
        self.assertIn('\\u003c/script', page)
        for path in ('https://vendor.invalid/audio.wav', 'audio/../../escape.wav', 'audio/evil:stream'):
            with self.assertRaises(LabError):
                write_player(self.directory, [sample], [{'sample_id': sample.id, 'alias': 'A', 'audio': path}], ['A'], 'mock')

    def test_env_example_contains_variable_names_only(self):
        lines = (REPOSITORY / '.env.example').read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(lines), 5)
        self.assertTrue(all(line and line.replace('_', '').isalpha() and line.isupper() for line in lines))


if __name__ == '__main__':
    unittest.main()
