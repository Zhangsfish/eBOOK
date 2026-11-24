"""Native iOS thread matrix and strict full/minimal waveform comparison."""
from pathlib import Path
import json
import math
import platform
import re
import shutil
import statistics
import subprocess
import threading
import uuid
from assets import REPO, SPIKE, verify
from make_minimal import create_candidate


def parse_native_metrics(text, kind, source_sha, threads=None):
    found = []
    for line in text.splitlines():
        if 'S02A_IOS_METRICS ' not in line:
            continue
        value, _ = json.JSONDecoder().raw_decode(line.split('S02A_IOS_METRICS ', 1)[1])
        if value.get('kind') == kind:
            found.append(value)
    if len(found) != 1:
        raise ValueError('Missing or ambiguous native metric record')
    result = found[0]
    if result.get('environment') != 'IOS_SIMULATOR' or result.get('genuine_ios_inference') is not True:
        raise ValueError('Desktop/compile-only output is not iOS inference')
    if result.get('run_context', {}).get('source_sha') != source_sha:
        raise ValueError('Metric source SHA mismatch')
    if kind == 'thread_benchmark':
        if result.get('threads') != threads or len(result.get('records', [])) != 7:
            raise ValueError('Incomplete thread/corpus measurement')
        if [r.get('speaker_id') for r in result['records'][:3]] != [3, 4, 58]:
            raise ValueError('Wrong measured speaker mapping')
        for record in result['records']:
            if record.get('sample_rate') != 24000 or record.get('frames', 0) <= 24000 or record.get('rms', 0) <= .001:
                raise ValueError('Missing valid original waveform evidence')
            if not re.fullmatch('[0-9a-f]{64}', record.get('wav_sha256', '')):
                raise ValueError('Missing waveform hash')
            if not math.isfinite(record['rms']) or not 0 <= record['first_callback_seconds'] <= record['generation_seconds']:
                raise ValueError('Invalid measured waveform/first callback')
            expected = record['frames'] / record['sample_rate']
            if not math.isclose(record['duration_seconds'], expected, rel_tol=1e-8):
                raise ValueError('Waveform duration/frame mismatch')
            if not math.isclose(record['rtf'], record['generation_seconds'] / expected, rel_tol=1e-8):
                raise ValueError('Inconsistent native RTF')
        ratios = [r['rtf'] for r in result['records']]
        if not all(math.isfinite(r) and r > 0 for r in ratios):
            raise ValueError('Invalid native timing')
        result['statistics'] = {'mean_rtf': statistics.mean(ratios),
            'p95_rtf_nearest_rank': sorted(ratios)[math.ceil(.95 * len(ratios)) - 1],
            'weighted_rtf': sum(r['generation_seconds'] for r in result['records']) /
                            sum(r['duration_seconds'] for r in result['records']),
            'peak_process_rss_bytes': max(r['process_peak_rss_cumulative_bytes'] for r in result['records'])}
    elif kind == 'minimal_equivalence':
        if result.get('original_cases') != 7 or any(len(result.get(name, [])) != 7 for name in
                ['full_wav_sha256', 'minimal_wav_sha256', 'full_frames', 'minimal_frames']):
            raise ValueError('Incomplete minimal/full comparison')
        if any(n <= 24000 for n in result['full_frames'] + result['minimal_frames']):
            raise ValueError('Invalid equivalence waveform frame count')
    return result


def run(model_dir):
    output = REPO / '.local-test-data/s02a' / ('ios-matrix-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'BLOCKED_IOS_RUNTIME', 'host': platform.system(), 'host_architecture': platform.machine(),
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'genuine_ios_inference': False, 'benchmarks': [], 'physical_device': 'NOT_RUN',
        'acoustic_audibility': 'NOT_MEASURED_NO_PHYSICAL_LOOPBACK',
        'session': {'status': 'NOT_RUN'}, 'license_clearance': 'UNRESOLVED_BINARY_AND_DATA_NOTICES'}
    metadata = output / 'result.json'
    def save(): metadata.write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    def execute(command, name, staged):
        result.setdefault('commands', []).append({'name': name, 'argv': command})
        print('S02A1_COMMAND_STARTED', name, flush=True)
        with (output / ('xcode-' + name + '.log')).open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, cwd=staged, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace')
            timer = threading.Timer(1500 if name != 'build' else 900, process.kill)
            timer.start()
            try:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    if any(marker in line for marker in ['S02A_IOS_', 'error:', '** BUILD', '** TEST']):
                        print(line.rstrip(), flush=True)
                code = process.wait()
            finally:
                timer.cancel()
        text = (output / ('xcode-' + name + '.log')).read_text(encoding='utf-8', errors='replace')
        return code, text
    try:
        if platform.system() != 'Darwin' or not shutil.which('xcodebuild') or not shutil.which('xcrun'):
            result['reason'] = 'No macOS/Xcode/iOS simulator runtime; no desktop substitution'
            return 3
        verify(model_dir)
        result['xcode_version'] = subprocess.check_output(['xcodebuild', '-version'], text=True).strip()
        result['host_cpu'] = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
        devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json'], text=True))
        candidates = [(runtime, device) for runtime, rows in devices['devices'].items() if '.iOS-' in runtime
                      for device in rows if device.get('isAvailable')]
        if not candidates:
            result['reason'] = 'No installed available iOS simulator; runtime installation is not performed'
            return 3
        runtime, device = next(((r, d) for r, d in candidates if d['state'] == 'Booted'), candidates[0])
        result['simulator_runtime'] = runtime
        result['simulator_name'] = device['name']
        staged = output / 'package'
        staged.mkdir()
        shutil.copy2(SPIKE / 'Package.swift', staged)
        for directory in ['Sources', 'Tests']:
            shutil.copytree(SPIKE / directory, staged / directory, ignore=shutil.ignore_patterns('__pycache__'))
        resources = staged / 'Tests/LocalTTSSpikeTests/Resources'
        shutil.copytree(model_dir, resources / 'kokoro')
        minimal = create_candidate(model_dir, resources / 'minimal', resources / 'minimal-model.json')
        result['minimal_manifest'] = {k: minimal[k] for k in ['canonical_manifest_sha256', 'unpacked_bytes', 'removed_bytes']}
        shutil.copy2(SPIKE / 'fixtures/corpus.json', resources / 'corpus.json')
        shutil.copy2(SPIKE / 'manifests/model.json', resources / 'model.json')
        (resources / 'run-context.json').write_text(json.dumps({'source_sha': result['source_sha'],
            'runtime_revision': '38016c6e0622e90bf417c35e8b47e0eb805af417'}), encoding='utf-8')
        common = ['xcodebuild', '-scheme', 'LocalTTSSpike', '-destination', 'platform=iOS Simulator,id=' + device['udid'],
            '-derivedDataPath', str(output / 'DerivedData'), '-parallel-testing-enabled', 'NO',
            '-clonedSourcePackagesDirPath', str(output / 'SourcePackages'), 'CODE_SIGNING_ALLOWED=NO']
        code, _ = execute(common + ['build-for-testing'], 'build', staged)
        result['build_exit_code'] = code
        if code:
            result.update(status='BLOCKED_NATIVE_BUILD', reason='Actual xcodebuild failed; inspect sanitized compiler diagnostics')
            return 3
        for threads in [1, 2, 3, 4]:
            method = 'LocalTTSSpikeTests/KokoroBenchmarkTests/testThreads' + str(threads)
            code, text = execute(common + ['-resultBundlePath', str(output / f'Threads{threads}.xcresult'),
                '-only-testing:' + method, 'test-without-building'], 'threads' + str(threads), staged)
            try:
                metric = parse_native_metrics(text, 'thread_benchmark', result['source_sha'], threads)
                if code:
                    raise ValueError('XCTest returned failure despite metric output')
                result['benchmarks'].append(metric)
                result['genuine_ios_inference'] = True
                print('S02A1_IOS_THREADS', threads, json.dumps(metric['statistics']), flush=True)
            except Exception as error:
                result.setdefault('failures', []).append({'threads': threads, 'xcode_exit': code, 'reason': str(error)})
            save()
        code, text = execute(common + ['-resultBundlePath', str(output / 'Equivalence.xcresult'),
            '-only-testing:LocalTTSSpikeTests/KokoroBenchmarkTests/testMinimalEquivalence',
            'test-without-building'], 'equivalence', staged)
        try:
            metric = parse_native_metrics(text, 'minimal_equivalence', result['source_sha'])
            if code or metric.get('bit_identical_pcm16_wav') is not True:
                raise ValueError('Minimal/full output equality not demonstrated')
            result['minimal_equivalence'] = metric
        except Exception as error:
            result['minimal_equivalence'] = {'status': 'NOT_PROVEN', 'xcode_exit': code, 'reason': str(error)}
        if result['benchmarks']:
            best = min(result['benchmarks'], key=lambda b: b['statistics']['weighted_rtf'])
            if best['statistics']['weighted_rtf'] >= 1:
                result['performance_gate'] = 'PERFORMANCE_NOT_READY'
                result['session'] = {'status': 'NOT_RUN_PERFORMANCE_NOT_READY',
                    'reason': 'Measured generation is slower than playback; bounded prebuffer cannot sustain it.'}
            else:
                result['performance_gate'] = 'READY_FOR_BOUNDED_SESSION_TRIAL'
                result['session'] = {'status': 'NOT_RUN_PENDING_BOUNDED_PLAYBACK_TRIAL', 'best_threads': best['threads']}
        good = len(result['benchmarks']) == 4 and result.get('minimal_equivalence', {}).get('bit_identical_pcm16_wav') is True
        result['status'] = 'PASS_NATIVE_INFERENCE_AND_EQUIVALENCE' if good else 'PARTIAL_NATIVE_RESULTS_WITH_BLOCKERS'
        return 0 if good else 3
    except Exception as error:
        result.update(status='BLOCKED_NATIVE_EXECUTION', reason=type(error).__name__ + ': ' + str(error)[:500])
        raise
    finally:
        save()
        print('S02A_IOS_RESULT', metadata, result['status'], flush=True)
