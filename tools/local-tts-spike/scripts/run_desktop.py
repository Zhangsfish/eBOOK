"""Real offline inference on the pinned original corpus, never on a book file."""
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import argparse
import ctypes
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
import uuid
import wave

from assets import REPO, SPIKE, sha256, verify

VOICES = [('zf_001', 3, 'A'), ('zf_002', 4, 'B'), ('zm_009', 58, 'C')]
MAX_CHARACTERS = 240


def validate_request(text, speed):
    if not text.strip() or len(text) > MAX_CHARACTERS or not 0.5 <= speed <= 2.0:
        raise ValueError('Expected 1..240 characters and speed 0.5..2.0')


def peak_rss():
    if platform.system() == 'Windows':
        class Counters(ctypes.Structure):
            _fields_ = [('cb', ctypes.c_ulong), ('faults', ctypes.c_ulong)] + [(n, ctypes.c_size_t) for n in
                ['peak', 'current', 'qpp', 'qp', 'qnpp', 'qnp', 'page', 'peakpage']]
        item = Counters()
        item.cb = ctypes.sizeof(item)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        api = ctypes.WinDLL('psapi', use_last_error=True)
        api.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
        if not api.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(item), item.cb):
            raise OSError('GetProcessMemoryInfo failed')
        return item.peak
    import resource
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if platform.system() == 'Darwin' else value * 1024)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--session-seconds', type=int, default=0, choices=[0, 600, 900])
    args = parser.parse_args()
    integrity = verify(args.model_dir)
    for name, version in [('sherpa-onnx', '2.0.3'), ('sherpa-onnx-core', '2.0.3'), ('numpy', '1.26.4')]:
        if importlib.metadata.version(name) != version:
            raise RuntimeError('Use the pinned isolated runtime: ' + name)
    import numpy as np
    import sherpa_onnx
    corpus = json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases']
    root = (REPO / '.local-test-data/s02a' / ('desktop-' + uuid.uuid4().hex)).resolve()
    root.mkdir(parents=True, exist_ok=False)
    model = args.model_dir.resolve()
    kokoro = sherpa_onnx.OfflineTtsKokoroModelConfig(model=str(model / 'model.int8.onnx'),
        voices=str(model / 'voices.bin'), tokens=str(model / 'tokens.txt'), dict_dir=str(model / 'dict'),
        lexicon=','.join(str(model / p) for p in ['lexicon-us-en.txt', 'lexicon-zh.txt']))
    config = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=kokoro,
        provider='cpu', num_threads=4), rule_fsts=','.join(str(model / p) for p in
        ['date-zh.fst', 'number-zh.fst', 'phone-zh.fst']), max_num_sentences=1)
    if not config.validate():
        raise RuntimeError('Invalid configuration')
    start = time.perf_counter()
    engine = sherpa_onnx.OfflineTts(config)
    init = time.perf_counter() - start
    if engine.num_speakers != 103:
        raise RuntimeError('Wrong model')
    print('S02A_MODEL_INITIALIZED', f'seconds={init:.6f}', flush=True)
    result = {'status': 'RUNNING', 'environment': 'WINDOWS_DESKTOP_CPU' if platform.system() == 'Windows' else 'DESKTOP_CPU',
        'genuine_ios_inference': False, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_file_sha256': {p.name: sha256(p) for p in [Path(__file__), SPIKE / 'scripts/assets.py']},
        'platform': platform.platform(), 'cpu': platform.processor(), 'python': platform.python_version(),
        'sherpa_onnx': sherpa_onnx.__version__, 'numpy': np.__version__, 'threads': 4,
        'model_integrity': integrity, 'model_initialization_seconds': init,
        'initialization_cache_state': 'Fresh process after hash verification; OS file cache NOT cold-controlled',
        'records': [], 'session': {'status': 'NOT_RUN', 'requested_audio_seconds': args.session_seconds},
        'private_inputs_read': 0, 'cloud_api_calls': 0, 'paid_calls': 0}
    output = root / 'metrics.json'

    def synthesize(case, voice, sid, label, index):
        text = case['text']
        validate_request(text, 1.0)
        begin = time.perf_counter()
        callbacks = []
        def callback(samples, progress):
            callbacks.append((time.perf_counter() - begin, float(progress), len(samples)))
            return 1
        generated = engine.generate(text=text, sid=sid, speed=1.0, callback=callback)
        elapsed = time.perf_counter() - begin
        samples = np.asarray(generated.samples, dtype=np.float32)
        rate = int(generated.sample_rate)
        if rate != 24000 or not len(samples) or not np.isfinite(samples).all():
            raise RuntimeError('Invalid waveform')
        rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
        if rms <= 0.001 or not callbacks or callbacks[-1][1] < 0.999:
            raise RuntimeError('Silent or incomplete waveform')
        pcm = np.rint(np.clip(samples, -1, 1) * 32767).astype('<i2')
        path = root / f'{index:04d}-{label}-{case["id"]}.wav'
        with wave.open(str(path), 'wb') as target:
            target.setnchannels(1); target.setsampwidth(2); target.setframerate(rate); target.writeframes(pcm.tobytes())
        return {'voice': voice, 'speaker_id': sid, 'anonymous_label': label, 'fixture_id': case['id'],
            'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'characters': len(text), 'speed': 1.0,
            'generation_seconds': elapsed, 'first_callback_seconds': callbacks[0][0],
            'duration_seconds': len(samples) / rate, 'rtf': elapsed / (len(samples) / rate),
            'sample_rate': rate, 'channels': 1, 'bits_per_sample': 16, 'frames': len(samples), 'rms': rms,
            'completed_fraction': callbacks[-1][1], 'callback_chunks': len(callbacks),
            'process_peak_rss_cumulative_bytes': peak_rss(), 'wav_sha256': sha256(path), 'wav_bytes': path.stat().st_size,
            'wav_local_name': path.name, 'status': 'GENERATED_REAL_DESKTOP'}, path

    jobs = [(corpus[0], *v) for v in VOICES] + [(c, *VOICES[0]) for c in corpus[1:]]
    for index, (case, voice, sid, label) in enumerate(jobs):
        record, _ = synthesize(case, voice, sid, label, index)
        result['records'].append(record)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('S02A_AUDIO', label, case['id'], f'duration={record["duration_seconds"]:.3f}', f'rtf={record["rtf"]:.4f}', flush=True)
    if len({r['wav_sha256'] for r in result['records'][:3]}) != 3:
        raise RuntimeError('Speaker waveforms unexpectedly identical')
    if args.session_seconds:
        queue = deque()
        spoken = 0.0
        started = time.perf_counter()
        session_rows = []
        while spoken < args.session_seconds:
            case = corpus[len(session_rows) % len(corpus)]
            row, path = synthesize(case, *VOICES[0], 1000 + len(session_rows))
            spoken += row['duration_seconds']
            session_rows.append(row)
            queue.append(path)
            if len(queue) > 3:
                # Only files created by this fresh run can enter this queue.
                queue.popleft().unlink()
        result['session'] = {'status': 'GENERATED_BOUNDED_AUDIO_NOT_REALTIME_PLAYBACK',
            'requested_audio_seconds': args.session_seconds, 'generated_audio_seconds': spoken,
            'wall_seconds': time.perf_counter() - started, 'max_retained_session_wavs': 3, 'records': session_rows}
    result['status'] = 'PASS_DESKTOP_ONLY'
    result['process_peak_rss_cumulative_bytes'] = peak_rss()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('S02A_METRICS_FILE', output, flush=True)


if __name__ == '__main__':
    main()
