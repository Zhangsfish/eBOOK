"""Genuine speech using the pinned author's unchanged Mandarin/English frontend.

No phoneme construction, network synthesis or model replacement is performed.
Generated files stay in ignored storage; native exported IDs are diagnostic only.
"""
from pathlib import Path
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
import uuid
import wave

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[4]
SPIKE = REPO / 'tools/local-tts-spike'
sys.path.insert(0, str(SPIKE / 's02a2/scripts'))
from model_assets import manifest, verify, sha256
from benchmark_desktop import peak_rss, statistics_for


def write_wave(path, samples, np):
    samples = np.asarray(samples, dtype=np.float32).reshape(-1)
    if not 22050 < len(samples) < 22050 * 120 or not np.isfinite(samples).all():
        raise ValueError('Invalid model waveform')
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    if rms <= .001:
        raise ValueError('Silent output is not speech evidence')
    pcm = np.rint(np.clip(samples, -1, 1) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(22050)
        out.writeframes(pcm.tobytes())
    with wave.open(str(path), 'rb') as check:
        assert len(check.readframes(len(samples))) == len(samples) * 2
    return {'sample_rate': 22050, 'frames': len(samples), 'duration_seconds': len(samples) / 22050,
            'rms': rms, 'float_peak': float(np.max(np.abs(samples))),
            'clipped_sample_fraction': float(np.mean(np.abs(samples) > 1)),
            'wav_local_name': path.name, 'wav_sha256': sha256(path), 'wav_bytes': path.stat().st_size}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--threads', type=int, choices=[1, 2, 4], default=4)
    args = parser.parse_args()
    integrity = verify(args.model_dir, manifest('suxin'))
    model_dir = args.model_dir.resolve()
    expected = {'numpy': '1.26.4', 'onnxruntime': '1.20.1', 'pypinyin': '0.55.0',
                'piper-tts': '1.8.0', 'pathvalidate': '3.3.1'}
    versions = {name: importlib.metadata.version(name) for name in expected}
    if versions != expected or sys.prefix == sys.base_prefix:
        raise RuntimeError('Use the new approved isolated pinned environment')
    sys.path.insert(0, str(model_dir))
    imported = time.perf_counter()
    import numpy as np
    from suxin_tts import SuxinTTS
    import_seconds = time.perf_counter() - imported
    corpus_path = SPIKE / 'fixtures/corpus.json'
    corpus = json.loads(corpus_path.read_text(encoding='utf-8'))['cases']
    output = REPO / '.local-test-data/s02a2/s02a3/outputs' / ('suxin-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    metadata = output / 'metrics.json'
    result = {'status': 'RUNNING', 'environment': 'WINDOWS_DESKTOP_CPU',
        'model': 'Suxin-Light int8-excldec', 'voice': 'single_speaker_author_default',
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'execution_worktree_dirty': bool(subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain'])),
        'source_file_sha256': {Path(__file__).name: sha256(Path(__file__)),
                              'benchmark_desktop.py': sha256(SPIKE / 's02a2/scripts/benchmark_desktop.py'),
                              'model_assets.py': sha256(SPIKE / 's02a2/scripts/model_assets.py')},
        'author_revision': manifest('suxin')['source_revision'], 'model_integrity': integrity,
        'corpus_sha256': sha256(corpus_path), 'python': platform.python_version(),
        'platform': platform.platform(), 'cpu': platform.processor(), 'packages': versions,
        'threads': args.threads, 'speed': 1.0, 'noise_scale': 0.0, 'noise_w': 0.0,
        'normalize_audio': False, 'author_code_modified': False,
        'entrypoint': 'SuxinTTS.from_pretrained + synthesize_long',
        'genuine_audio_generation': False, 'genuine_ios_inference': False,
        'end_to_end_native_text': False, 'first_audible_output': 'NOT_RUN_NO_PLAYBACK_PROBE',
        'human_quality': 'OWNER_LISTENING_PENDING', 'cloud_api_calls': 0,
        'private_book_inputs': 0, 'import_seconds': import_seconds, 'records': []}
    prepared = {'frontend_mode': 'AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS',
        'end_to_end_native_text': False, 'author_revision': result['author_revision'],
        'corpus_sha256': result['corpus_sha256'], 'records': []}
    tts = None
    try:
        start = time.perf_counter()
        tts = SuxinTTS.from_pretrained(model_dir, intra_op_num_threads=args.threads)
        result['model_initialization_seconds'] = time.perf_counter() - start
        result['actual_providers'] = tts.session.get_providers()
        if tts.sample_rate != 22050:
            raise ValueError('Unexpected author sample rate')
        for case in corpus:
            start = time.perf_counter()
            audio = tts.synthesize_long(case['text'])
            elapsed = time.perf_counter() - start
            if audio is None:
                raise ValueError('No audio for ' + case['id'])
            saved = write_wave(output / (case['id'] + '.wav'), audio, np)
            # The exact author's prepare call, without hand-built/edited IDs.
            ids, phonemes = tts.frontend.prepare(case['text'])
            text_hash = hashlib.sha256(case['text'].encode('utf-8')).hexdigest()
            row = dict(saved, fixture_id=case['id'], text_sha256=text_hash,
                generation_seconds=elapsed, rtf=elapsed / saved['duration_seconds'],
                process_peak_rss_cumulative_bytes=peak_rss(),
                frontend_missing_phonemes=sorted(set(phonemes) - set(tts.frontend.phoneme_id_map)),
                first_callback_seconds=None, speaker_id=0, speed=1.0)
            result['records'].append(row)
            prepared['records'].append({'fixture_id': case['id'], 'text_sha256': text_hash,
                'ids': ids, 'phonemes': phonemes,
                'author_frontend_method': 'MixedFrontend.prepare(original_unmodified_text)',
                'frontend_missing_phonemes': row['frontend_missing_phonemes']})
            metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            print('REAL_SUXIN_WAV', case['id'], 'seconds', round(saved['duration_seconds'], 3),
                  'rtf', round(row['rtf'], 4), flush=True)
        result['statistics'] = statistics_for(result['records'])
        result['first_case_complete_ready_seconds_including_model_init'] = (
            result['model_initialization_seconds'] + result['records'][0]['generation_seconds'])
        async def stream_probe():
            async def tokens():
                for char in corpus[0]['text']:
                    yield char
            start = time.perf_counter(); first = None; chunks = []
            async for audio in tts.synthesize_stream_from_tokens(tokens()):
                if first is None:
                    first = time.perf_counter() - start
                chunks.append(np.asarray(audio))
            elapsed = time.perf_counter() - start
            saved = write_wave(output / 'narration-author-stream.wav', np.concatenate(chunks), np)
            return dict(saved, first_emitted_chunk_seconds=first, generation_seconds=elapsed,
                        chunks=len(chunks), token_feed='Instant original text; not an LLM/network stream',
                        playback='NOT_RUN', warmed_engine=True)
        result['author_stream_probe'] = asyncio.run(stream_probe())
        (output / 'author-precomputed-ids.json').write_text(json.dumps(prepared, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result['prepared_ids_sha256'] = sha256(output / 'author-precomputed-ids.json')
        result.update(status='PASS_DESKTOP_ONLY_REAL_WAV', genuine_audio_generation=True)
    except Exception as error:
        result.update(status='BLOCKED_DESKTOP_SYNTHESIS', error=type(error).__name__ + ': ' + str(error)[:600])
        raise
    finally:
        if tts is not None:
            tts.close()
        result['peak_process_rss_bytes'] = peak_rss()
        metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('SUXIN_RESULT', metadata, result['status'], flush=True)


if __name__ == '__main__':
    main()
