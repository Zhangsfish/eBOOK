"""Real candidate synthesis; fixed original text, no mock or network TTS."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import statistics
import subprocess
import sys
import time
import uuid
import wave
from model_assets import SPIKE, REPO, LOCAL, manifest, verify, sha256

sys.path.insert(0, str(SPIKE / 'scripts'))
from run_desktop import peak_rss, validate_request


def statistics_for(rows):
    rtf = [r['rtf'] for r in rows]
    return {'mean_rtf': statistics.mean(rtf),
            'p95_rtf_nearest_rank': sorted(rtf)[math.ceil(.95 * len(rtf)) - 1],
            'weighted_rtf': sum(r['generation_seconds'] for r in rows) / sum(r['duration_seconds'] for r in rows),
            'peak_process_rss_bytes': max(r['process_peak_rss_cumulative_bytes'] for r in rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['matcha'], required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--threads', type=int, choices=[1, 2, 3, 4], default=4)
    args = parser.parse_args()
    value = manifest(args.model)
    integrity = verify(args.model_dir, value)
    if importlib.metadata.version('sherpa-onnx') != '2.0.3':
        raise RuntimeError('Use the existing approved sherpa-onnx 2.0.3 environment')
    import numpy as np
    import sherpa_onnx
    directory = args.model_dir.resolve()
    model = sherpa_onnx.OfflineTtsMatchaModelConfig(
        acoustic_model=str(directory / 'model-steps-3.onnx'), vocoder=str(directory / 'vocos-22khz-univ.onnx'),
        lexicon=str(directory / 'lexicon.txt'), tokens=str(directory / 'tokens.txt'))
    config = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        matcha=model, num_threads=args.threads, provider='cpu'),
        rule_fsts=','.join(str(directory / n) for n in ['phone.fst', 'date.fst', 'number.fst']),
        max_num_sentences=1)
    if not config.validate():
        raise RuntimeError('Invalid native Matcha configuration')
    output = LOCAL / 'outputs' / ('matcha-desktop-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'RUNNING', 'environment': 'WINDOWS_DESKTOP_CPU' if platform.system() == 'Windows' else 'DESKTOP_CPU',
        'genuine_ios_inference': False, 'model': value['model'], 'voice': 'single_female_sid0',
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'execution_worktree_dirty': bool(subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain'])),
        'source_file_sha256': {Path(__file__).name: sha256(Path(__file__)), 'model_assets.py': sha256(Path(__file__).with_name('model_assets.py'))},
        'corpus_sha256': sha256(SPIKE / 'fixtures/corpus.json'), 'model_integrity': integrity,
        'python': platform.python_version(), 'platform': platform.platform(), 'cpu': platform.processor(),
        'sherpa_onnx': sherpa_onnx.__version__, 'numpy': np.__version__, 'threads': args.threads,
        'first_audible_output': 'NOT_MEASURED_NO_PLAYBACK_PROBE', 'records': [],
        'human_quality': 'OWNER_LISTENING_PENDING', 'cloud_api_calls': 0, 'private_book_inputs': 0}
    metadata = output / 'metrics.json'
    try:
        started = time.perf_counter()
        engine = sherpa_onnx.OfflineTts(config)
        result['model_initialization_seconds'] = time.perf_counter() - started
        if engine.num_speakers != 1:
            raise RuntimeError('Expected the named single-speaker Matcha model')
        warm_start = time.perf_counter()
        engine.generate(text='清风吹过窗边。', sid=0, speed=1)
        result['warmup_seconds'] = time.perf_counter() - warm_start
        corpus = json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases']
        for case in corpus:
            validate_request(case['text'], 1)
            start = time.perf_counter()
            callbacks = []
            def callback(samples, progress):
                if len(samples): callbacks.append((time.perf_counter() - start, float(progress)))
                return 1
            audio = engine.generate(text=case['text'], sid=0, speed=1, callback=callback)
            elapsed = time.perf_counter() - start
            samples = np.asarray(audio.samples, dtype=np.float32)
            if int(audio.sample_rate) != 22050 or not len(samples) or not np.isfinite(samples).all():
                raise RuntimeError('Invalid actual waveform')
            rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
            if rms <= .001 or not callbacks or callbacks[-1][1] < .999:
                raise RuntimeError('Silent or incomplete model output')
            path = output / (case['id'] + '.wav')
            pcm = np.rint(np.clip(samples, -1, 1) * 32767).astype('<i2')
            with wave.open(str(path), 'wb') as target:
                target.setnchannels(1); target.setsampwidth(2); target.setframerate(22050)
                target.writeframes(pcm.tobytes())
            duration = len(samples) / 22050
            row = {'fixture_id': case['id'], 'text_sha256': hashlib.sha256(case['text'].encode()).hexdigest(),
                'speaker_id': 0, 'speed': 1, 'generation_seconds': elapsed,
                'first_callback_seconds': callbacks[0][0], 'duration_seconds': duration, 'rtf': elapsed / duration,
                'sample_rate': 22050, 'frames': len(samples), 'rms': rms,
                'process_peak_rss_cumulative_bytes': peak_rss(), 'wav_local_name': path.name,
                'wav_sha256': sha256(path), 'wav_bytes': path.stat().st_size}
            result['records'].append(row)
            metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            print('REAL_MATCHA_DESKTOP', case['id'], 'seconds', round(duration, 3), 'rtf', round(row['rtf'], 4), flush=True)
        result['statistics'] = statistics_for(result['records'])
        result['status'] = 'PASS_DESKTOP_ONLY_REAL_WAV'
    except Exception as error:
        result.update(status='BLOCKED_DESKTOP', reason=type(error).__name__ + ': ' + str(error)[:400])
        raise
    finally:
        metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('S02A2_DESKTOP_RESULT', metadata, result['status'], flush=True)


if __name__ == '__main__': main()
