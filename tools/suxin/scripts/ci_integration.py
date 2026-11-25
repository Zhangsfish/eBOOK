"""Real iOS frontend/integration checks; no host inference or signing substitute."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', choices=['frontend', 'all'], default='frontend')
    args = parser.parse_args()
    build = ROOT / 'build'; build.mkdir(exist_ok=True)
    env = dict(os.environ)
    if Path('/Applications/Xcode_16.4.app').is_dir():
        env['DEVELOPER_DIR'] = '/Applications/Xcode_16.4.app/Contents/Developer'
    def output(argv):
        return subprocess.check_output(argv, cwd=ROOT, env=env, text=True).strip()
    devices = json.loads(output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))
    choices = [(runtime, device) for runtime, rows in devices['devices'].items() if '.iOS-' in runtime
               for device in rows if device.get('isAvailable')]
    if not choices:
        raise RuntimeError('No installed iOS simulator; no installation attempted')
    runtime, device = next(((r, d) for r, d in choices if d['state'] == 'Booted'), choices[0])
    if device['state'] != 'Booted':
        subprocess.run(['xcrun', 'simctl', 'boot', device['udid']], env=env, check=True)
    with (build / 's02b-boot.log').open('w') as log:
        subprocess.run(['xcrun', 'simctl', 'bootstatus', device['udid'], '-b'], env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
    common = ['xcodebuild', '-project', 'eBOOK.xcodeproj', '-scheme', 'eBOOK',
              '-destination', 'id=' + device['udid'], '-derivedDataPath', 'build/S02B-DerivedData',
              '-parallel-testing-enabled', 'NO', 'CODE_SIGNING_ALLOWED=NO']
    def execute(argv, name, timeout):
        print('S02B_START', name, flush=True)
        with (build / ('s02b-' + name + '.log')).open('w') as log:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        if result.returncode:
            print('\n'.join((build / ('s02b-' + name + '.log')).read_text().splitlines()[-65:]), flush=True)
        return result.returncode
    if execute(common + ['-configuration', 'Debug', 'build-for-testing'], 'build', 900):
        raise RuntimeError('Actual App/test compilation failed')
    command = common + ['-configuration', 'Debug', '-resultBundlePath', 'build/S02B-tests.xcresult']
    if args.scope == 'frontend':
        command += ['-only-testing:EBookTests/SuxinFrontendTests']
    code = execute(command + ['test-without-building'], 'test', 1500)
    raw = output(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', 'build/S02B-tests.xcresult', '--format', 'json'])
    summary = json.loads(raw)
    (build / 's02b-test-summary.json').write_text(raw + '\n')
    result = {'source_sha': output(['git', 'rev-parse', 'HEAD']), 'scope': args.scope,
              'xcode': output(['xcodebuild', '-version']), 'simulator_runtime': runtime,
              'simulator_name': device['name'], 'host_architecture': output(['uname', '-m']),
              'actual_counts': {key: summary[key] for key in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']},
              'neural_audio_generation': False, 'physical_device': 'NOT_RUN',
              'status': 'PASS_NATIVE_FRONTEND_ONLY' if not code else 'FAIL_ACTUAL_XCTEST'}
    (build / 's02b-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    if args.scope == 'frontend' and (summary['totalTestCount'] != 3 or summary['skippedTests'] != 0):
        raise RuntimeError('All three native frontend methods must actually execute')
    if code or summary['failedTests']:
        raise RuntimeError('Actual native test failure')


if __name__ == '__main__':
    main()
