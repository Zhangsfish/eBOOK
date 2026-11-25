"""One bounded Kokoro/CoreML attempt or isolated alternative iOS proof.

No desktop substitution, production project edits, tool installation, signing,
or media upload. Raw model/audio/profile/build files remain ignored.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import signal
import statistics
import subprocess
import threading
import uuid
from model_assets import SPIKE, REPO, LOCAL, manifest, verify, sha256

import sys
sys.path.insert(0, str(SPIKE / 'scripts'))
from assets import verify as verify_kokoro

PINS = {'sherpa-onnx': '38016c6e0622e90bf417c35e8b47e0eb805af417',
        'onnxruntime-libs': '8ebc5ebf92190903c274a7621ba4c96a732335ec'}
METHODS = {'kokoro-final': [('providers', 'testRuntimeProviders', 120),
                          ('cpu', 'testKokoroCPUFinal', 600), ('coreml', 'testKokoroCoreMLFinal', 720)],
           'matcha': [('matcha2', 'testMatchaThreads2', 600), ('matcha4', 'testMatchaThreads4', 600)],
           'suxin-backend': [('suxin', 'testSuxinBackendOnly', 600)]}


def parse_metric(text, source_sha, kind):
    rows = []
    for line in text.splitlines():
        if 'S02A2_METRICS ' not in line:
            continue
        value, _ = json.JSONDecoder().raw_decode(line.split('S02A2_METRICS ', 1)[1])
        if value.get('kind') == kind:
            rows.append(value)
    if len(rows) != 1:
        raise ValueError('Missing/duplicate actual native metric')
    value = rows[0]
    if value.get('environment') != 'IOS_SIMULATOR' or value.get('run_context', {}).get('source_sha') != source_sha:
        raise ValueError('Wrong platform/source; macOS or desktop is not iOS')
    if kind == 'runtime_providers':
        return value
    genuine = value.get('genuine_ios_graph_inference') if kind == 'suxin_backend' else value.get('genuine_ios_inference')
    if genuine is not True:
        raise ValueError('No actual native waveform inference')
    corpus = json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases']
    records = value.get('records', [])
    if [r.get('fixture_id') for r in records] != [c['id'] for c in corpus]:
        raise ValueError('Incomplete original corpus')
    if kind == 'suxin_backend' and (value.get('end_to_end_native_text') is not False or
            value.get('frontend_mode') != 'AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS'):
        raise ValueError('Backend-only IDs cannot prove a native text frontend')
    expected_rate = 24000 if kind == 'kokoro_pair' else 22050
    for row in records:
        if row.get('sample_rate') != expected_rate or row.get('frames', 0) <= expected_rate:
            raise ValueError('Invalid actual waveform frames/rate')
        duration = row['frames'] / expected_rate
        if not math.isclose(row['duration_seconds'], duration, rel_tol=1e-8):
            raise ValueError('Inconsistent waveform duration')
        if not math.isfinite(row['rtf']) or row['rtf'] <= 0 or not math.isclose(row['rtf'], row['generation_seconds'] / duration, rel_tol=1e-8):
            raise ValueError('Invalid measured RTF')
        if not math.isfinite(row.get('rms', 0)) or row['rms'] <= .001 or not re.fullmatch('[0-9a-f]{64}', row.get('wav_sha256', '')):
            raise ValueError('Silent/invalid/unhashed waveform')
    ratios = [r['rtf'] for r in records]
    value['statistics'] = {'mean_rtf': statistics.mean(ratios),
        'p95_rtf_nearest_rank': sorted(ratios)[math.ceil(.95 * len(ratios)) - 1],
        'weighted_rtf': sum(r['generation_seconds'] for r in records) / sum(r['duration_seconds'] for r in records),
        'peak_process_rss_bytes': max(r['process_peak_rss_cumulative_bytes'] for r in records)}
    return value


def coreml_execution(profile):
    """Listing/registration alone never proves execution or ANE acceleration."""
    if profile.get('status') != 'ACTUAL_ORT_PROFILE_INSPECTED':
        return 'NOT_PROVEN_NODE_ASSIGNMENT'
    counts = profile.get('provider_node_event_counts', {})
    if counts.get('CoreMLExecutionProvider', 0) <= 0:
        return 'CPU_FALLBACK_NO_COREML_NODE_EVENTS'
    return 'COREML_NODE_EVENTS_OBSERVED_ANE_NOT_MEASURED'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=METHODS, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--prepared-ids', type=Path)
    args = parser.parse_args()
    output = LOCAL / ('native-' + args.phase + '-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    source_sha = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    result = {'status': 'RUNNING', 'phase': args.phase, 'source_sha': source_sha,
        'host': platform.system(), 'host_architecture': platform.machine(), 'measurements': [],
        'physical_device': 'DEVICE_NOT_RUN', 'thermal': 'DEVICE_NOT_RUN', 'battery': 'DEVICE_NOT_RUN',
        'locked_screen_playback': 'DEVICE_NOT_RUN', 'human_quality': 'OWNER_LISTENING_PENDING',
        'genuine_ios_inference': False, 'genuine_ios_graph_inference': False,
        'production_app_changed': False, 'cloud_tts_calls': 0}
    metadata = output / 'result.json'
    def save(): metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    def execute(command, name, timeout, directory):
        result.setdefault('commands', []).append({'name': name, 'argv': command, 'timeout_seconds': timeout})
        print('S02A2_COMMAND_STARTED', name, flush=True)
        with (output / ('xcode-' + name + '.log')).open('w', encoding='utf-8') as target:
            process = subprocess.Popen(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding='utf-8', errors='replace', start_new_session=True)
            timed_out = []
            def stop():
                timed_out.append(True)
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            timer = threading.Timer(timeout, stop); timer.start()
            try:
                for line in process.stdout:
                    target.write(line); target.flush()
                    if any(s in line for s in ['S02A2_', 'error:', '** BUILD', '** TEST', 'CoreMLExecutionProvider::GetCapability']):
                        print(line.rstrip(), flush=True)
                code = process.wait()
            finally:
                timer.cancel()
        if timed_out: result.setdefault('timeouts', []).append(name)
        return code, (output / ('xcode-' + name + '.log')).read_text(encoding='utf-8', errors='replace')
    try:
        if platform.system() != 'Darwin' or not shutil.which('xcodebuild') or not shutil.which('xcrun'):
            result.update(status='BLOCKED_IOS_RUNTIME', reason='No macOS/Xcode; no host-synthesis substitution')
            return 3
        if args.phase == 'kokoro-final':
            verify_kokoro(args.model_dir)
        else:
            verify(args.model_dir, manifest('matcha' if args.phase == 'matcha' else 'suxin'))
        devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json'], text=True))
        available = [(r, d) for r, rows in devices['devices'].items() if '.iOS-' in r for d in rows if d.get('isAvailable')]
        if not available: raise RuntimeError('No installed simulator; no runtime installation attempted')
        runtime, device = next(((r, d) for r, d in available if d['state'] == 'Booted'), available[0])
        result.update(simulator_runtime=runtime, simulator_name=device['name'],
            xcode_version=subprocess.check_output(['xcodebuild', '-version'], text=True).strip(),
            host_cpu=subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip())
        staged = output / 'package'; staged.mkdir()
        shutil.copy2(SPIKE / 'Package.swift', staged)
        for name in ['Sources', 'Tests']:
            shutil.copytree(SPIKE / name, staged / name, ignore=shutil.ignore_patterns('__pycache__'))
        resources = staged / 'Tests/LocalTTSSpikeTests/Resources'
        label = {'kokoro-final': 'kokoro', 'matcha': 'matcha', 'suxin-backend': 'suxin'}[args.phase]
        shutil.copytree(args.model_dir, resources / label)
        pins = SPIKE / ('manifests/model.json' if label == 'kokoro' else 's02a2/manifests/' + label + '.json')
        shutil.copy2(pins, resources / ('model.json' if label == 'kokoro' else label + '-model.json'))
        shutil.copy2(SPIKE / 'fixtures/corpus.json', resources / 'corpus.json')
        if label == 'suxin':
            if not args.prepared_ids or not args.prepared_ids.is_file(): raise ValueError('Actual author-prepared IDs required; no native frontend substitution')
            sys.path.insert(0, str(SPIKE / 's02a3/scripts'))
            from validate_precomputed import validate_precomputed
            result['precomputed_frontend_provenance'] = validate_precomputed(args.prepared_ids)
            shutil.copy2(args.prepared_ids, resources / 'suxin-ids.json')
        context = {'source_sha': source_sha, 'phase': args.phase, 'runtime_revision': PINS['sherpa-onnx'],
            'corpus_sha256': sha256(resources / 'corpus.json')}
        if label == 'suxin': context['precomputed_frontend_provenance'] = result['precomputed_frontend_provenance']
        (resources / 's02a2-context.json').write_text(json.dumps(context), encoding='utf-8')
        common = ['xcodebuild', '-scheme', 'LocalTTSSpike', '-destination', 'platform=iOS Simulator,id=' + device['udid'],
            '-derivedDataPath', str(output / 'DerivedData'), '-clonedSourcePackagesDirPath', str(output / 'SourcePackages'),
            '-parallel-testing-enabled', 'NO', 'CODE_SIGNING_ALLOWED=NO']
        code, _ = execute(common + ['-resolvePackageDependencies'], 'resolve', 300, staged)
        if code: raise RuntimeError('Pinned dependency resolution failed')
        actual_pins = {}
        for name, expected in PINS.items():
            actual = subprocess.check_output(['git', '-C', str(output / 'SourcePackages/checkouts' / name), 'rev-parse', 'HEAD'], text=True).strip()
            if actual != expected: raise RuntimeError('Transitive source revision mismatch: ' + name)
            actual_pins[name] = actual
        result['actual_resolved_source_revisions'] = actual_pins
        code, _ = execute(common + ['-disableAutomaticPackageResolution', 'build-for-testing'], 'build', 600, staged)
        result['build_exit_code'] = code
        if code:
            result['status'] = 'BLOCKED_NATIVE_BUILD'; return 3
        save()
        for name, method, timeout in METHODS[args.phase]:
            code, log = execute(common + ['-disableAutomaticPackageResolution',
                '-resultBundlePath', str(output / (name + '.xcresult')),
                '-only-testing:LocalTTSSpikeTests/MobileCandidateTests/' + method,
                'test-without-building'], name, timeout, staged)
            kind = {'providers': 'runtime_providers', 'cpu': 'kokoro_pair', 'coreml': 'kokoro_pair',
                    'matcha2': 'matcha', 'matcha4': 'matcha', 'suxin': 'suxin_backend'}[name]
            try:
                value = parse_metric(log, source_sha, kind)
                if code: raise ValueError('XCTest failed despite metric marker')
                if kind == 'kokoro_pair':
                    value['effective_coreml_execution'] = coreml_execution(value.get('profile', {}))
                    value['runtime_assignment_messages'] = [line[-1600:] for line in log.splitlines()
                        if 'CoreMLExecutionProvider::GetCapability' in line or 'VerifyEachNodeIsAssignedToAnEp' in line][:12]
                value['test_method'] = method
                result['measurements'].append(value)
                if kind in ['matcha', 'kokoro_pair']: result['genuine_ios_inference'] = True
                if kind == 'suxin_backend': result['genuine_ios_graph_inference'] = True
                print('S02A2_MEASURED', name, json.dumps(value.get('statistics', {})), flush=True)
            except Exception as error:
                result.setdefault('failures', []).append({'method': method, 'xcode_exit': code, 'reason': str(error)[:500]})
            save()
        result['status'] = 'COMPLETED_MEASUREMENTS_DEVICE_NOT_RUN' if not result.get('failures') else 'PARTIAL_MEASUREMENTS_WITH_BLOCKERS'
        if args.phase == 'kokoro-final': result['decision'] = 'KOKORO_DEVICE_PERFORMANCE_NOT_READY_STOP_OPTIMIZING'
        else: result['decision'] = 'EXPERIMENTAL_CANDIDATE_DEVICE_FRONTEND_LICENSE_AND_OWNER_GATES_PENDING'
        return 0 if not result.get('failures') else 3
    except Exception as error:
        result.update(status='BLOCKED_NATIVE_EXECUTION', reason=type(error).__name__ + ': ' + str(error)[:500])
        raise
    finally:
        save(); print('S02A2_NATIVE_RESULT', metadata, result['status'], flush=True)


if __name__ == '__main__': raise SystemExit(main())
