"""Stage the isolated Swift package and run real XCTest on an available simulator.

Does not modify the reader, install Xcode/runtimes or upload/download book text.
Absent Xcode writes BLOCKED_IOS_RUNTIME and exits 3; never falls back to desktop.
"""
from pathlib import Path
import argparse
import json
import platform
import shutil
import subprocess
import uuid
from assets import REPO, SPIKE, verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--benchmark-matrix', action='store_true')
    args = parser.parse_args()
    if args.benchmark_matrix:
        from run_matrix import run
        return run(args.model_dir)
    output = REPO / '.local-test-data/s02a' / ('ios-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'BLOCKED_IOS_RUNTIME', 'host': platform.system(),
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'xcodebuild': shutil.which('xcodebuild'), 'xcrun': shutil.which('xcrun'), 'genuine_ios_inference': False}
    metadata = output / 'result.json'
    if platform.system() != 'Darwin' or not result['xcodebuild'] or not result['xcrun']:
        result['reason'] = 'No macOS/Xcode/iOS simulator runtime on this host; no model inference attempted.'
        metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2)); print('S02A_IOS_RESULT', metadata)
        return 3
    verify(args.model_dir)
    devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json'], text=True))
    candidates = [d for runtime, rows in devices['devices'].items() if '.iOS-' in runtime for d in rows if d.get('isAvailable')]
    if not candidates:
        result['reason'] = 'No installed available iOS simulator device; no runtime installation performed.'
        metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2)); return 3
    simulator = next((d for d in candidates if d['state'] == 'Booted'), candidates[0])
    staged = output / 'package'
    staged.mkdir()
    shutil.copy2(SPIKE / 'Package.swift', staged)
    for folder in ['Sources', 'Tests']:
        shutil.copytree(SPIKE / folder, staged / folder)
    resources = staged / 'Tests/LocalTTSSpikeTests/Resources'
    shutil.copytree(args.model_dir, resources / 'kokoro')
    shutil.copy2(SPIKE / 'fixtures/corpus.json', resources / 'corpus.json')
    shutil.copy2(SPIKE / 'manifests/model.json', resources / 'model.json')
    (resources / 'run-context.json').write_text(json.dumps({'source_sha': result['source_sha'],
        'runtime_revision': '38016c6e0622e90bf417c35e8b47e0eb805af417'}), encoding='utf-8')
    command = ['xcodebuild', '-scheme', 'LocalTTSSpike', '-destination', 'platform=iOS Simulator,id=' + simulator['udid'],
        '-derivedDataPath', str(output / 'DerivedData'), '-resultBundlePath', str(output / 'Native.xcresult'),
        'CODE_SIGNING_ALLOWED=NO',
        '-only-testing:LocalTTSSpikeTests/KokoroInferenceTests/testActualOriginalMandarinInference', 'test']
    result['command'] = command
    result['xcode_version'] = subprocess.check_output(['xcodebuild', '-version'], text=True).strip()
    with (output / 'xcode-test.log').open('w', encoding='utf-8') as log:
        done = subprocess.run(command, cwd=staged, stdout=log, stderr=subprocess.STDOUT)
    lines = (output / 'xcode-test.log').read_text(encoding='utf-8', errors='replace').splitlines()
    marker = 'S02A_IOS_METRICS '
    metrics = [json.loads(line.split(marker, 1)[1]) for line in lines if marker in line]
    result['xcode_exit_code'] = done.returncode
    if done.returncode == 0 and len(metrics) == 1 and metrics[0]['environment'] == 'IOS_SIMULATOR' and len(metrics[0]['records']) == 7:
        result.update(status='PASS_ACTUAL_IOS_INFERENCE', genuine_ios_inference=True, metrics=metrics[0])
    else:
        result['reason'] = 'Native build/test failed or actual iOS waveform metrics missing; inspect local Xcode log.'
    metadata.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('S02A_IOS_RESULT', metadata, result['status'])
    return 0 if result['genuine_ios_inference'] else 3


if __name__ == '__main__':
    raise SystemExit(main())
