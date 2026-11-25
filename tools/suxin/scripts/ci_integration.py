"""Real iOS frontend/integration checks; no host inference or signing substitute."""
from pathlib import Path
import argparse
import json
import os
import hashlib
import plistlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', choices=['frontend', 'integration', 'all'], default='integration')
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
    subprocess.run([sys.executable, 'tools/suxin/scripts/inspect_runtime.py', '--verify-spm-dir',
                    'build/S02B-DerivedData/SourcePackages'], cwd=ROOT, env=env, check=True)
    if args.scope == 'all':
        app = build / 'S02B-DerivedData/Build/Products/Debug-iphonesimulator/eBOOK.app'
        subprocess.run(['xcrun', 'simctl', 'install', device['udid'], str(app)], env=env, check=True)
        container = Path(output(['xcrun', 'simctl', 'get_app_container', device['udid'], 'com.zhangsfish.ebook', 'data']))
        documents = container / 'Documents'; documents.mkdir(exist_ok=True)
        for source in [ROOT / '.local-test-data/synthetic_long_gb18030.txt', ROOT / 'Tests/Fixtures/sample_utf8.txt', ROOT / 'Tests/Fixtures/synthetic.epub']:
            shutil.copyfile(source, documents / source.name)
    command = common + ['-configuration', 'Debug', '-resultBundlePath', 'build/S02B-tests.xcresult']
    if args.scope == 'frontend':
        command += ['-only-testing:EBookTests/SuxinFrontendTests']
    elif args.scope == 'integration':
        command += ['-only-testing:EBookTests/SuxinFrontendTests', '-only-testing:EBookTests/SuxinIntegrationTests',
                    '-only-testing:EBookTests/SuxinStateTests']
    code = execute(command + ['test-without-building'], 'test', 1500)
    raw = output(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', 'build/S02B-tests.xcresult', '--format', 'json'])
    summary = json.loads(raw)
    (build / 's02b-test-summary.json').write_text(raw + '\n')
    details = output(['xcrun', 'xcresulttool', 'get', 'test-results', 'tests', '--path', 'build/S02B-tests.xcresult', '--format', 'json'])
    (build / 's02b-test-details.json').write_text(details + '\n')
    metrics = []
    for line in (build / 's02b-test.log').read_text().splitlines():
        if 'S02B_METRIC ' in line:
            metrics.append(json.loads(line.split('S02B_METRIC ', 1)[1]))
    neural = any(row.get('end_to_end_native_text') is True for row in metrics)
    result = {'source_sha': output(['git', 'rev-parse', 'HEAD']), 'scope': args.scope,
              'xcode': output(['xcodebuild', '-version']), 'simulator_runtime': runtime,
              'simulator_name': device['name'], 'host_architecture': output(['uname', '-m']),
              'actual_counts': {key: summary[key] for key in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']},
              'neural_audio_generation': neural, 'metrics': metrics, 'physical_device': 'NOT_RUN',
              'status': ('PASS_NATIVE_FRONTEND_ONLY' if args.scope == 'frontend' else 'PASS_NATIVE_INTEGRATION') if not code else 'FAIL_ACTUAL_XCTEST'}
    (build / 's02b-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    if args.scope == 'frontend' and (summary['totalTestCount'] != 3 or summary['skippedTests'] != 0):
        raise RuntimeError('All three native frontend methods must actually execute')
    if args.scope == 'integration' and (summary['totalTestCount'] != 11 or summary['skippedTests'] != 0):
        raise RuntimeError('All eleven integration methods must actually execute')
    if args.scope != 'frontend' and (not neural or len(metrics) != 2):
        raise RuntimeError('Missing actual native waveform or PCM mixer evidence')
    if code or summary['failedTests']:
        raise RuntimeError('Actual native test failure')
    if args.scope == 'all':
        container = Path(output(['xcrun', 'simctl', 'get_app_container', device['udid'], 'com.zhangsfish.ebook', 'data']))
        source = container / 'Documents/.s00-render-metrics-long.json'
        if not source.exists():
            raise RuntimeError('No actual long-reader regression metrics')
        shutil.copyfile(source, build / 'reader-metrics.json')
        subprocess.run([sys.executable, 'scripts/check_reader_metrics.py'], cwd=ROOT, env=env, check=True)
        shutil.copyfile(build / 'reader-metrics-summary.json', build / 's02b-reader-metrics-summary.json')
        archive = ['xcodebuild', '-project', 'eBOOK.xcodeproj', '-scheme', 'eBOOK', '-configuration', 'Release',
                   '-destination', 'generic/platform=iOS', '-archivePath', 'build/S02B-device.xcarchive',
                   '-derivedDataPath', 'build/S02B-DerivedData', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO', 'archive']
        if execute(archive, 'device-archive', 900):
            raise RuntimeError('Actual unsigned arm64 Release archive failed')
        app = build / 'S02B-device.xcarchive/Products/Applications/eBOOK.app'
        manifest = json.loads((app / 'Suxin/manifest.json').read_text())
        for item in manifest['files']:
            data = (app / 'Suxin' / item['path']).read_bytes()
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Archived model resource mismatch')
        allowed = {app / 'Suxin/author-LICENSE.txt', app / 'Suxin/pypinyin-LICENSE.txt'}
        if set(app.rglob('*.txt')) != allowed or list(app.rglob('*.epub')) or list(app.rglob('*.wav')):
            raise ValueError('Unexpected book/audio/text in release bundle')
        info = plistlib.loads((app / 'Info.plist').read_bytes())
        archs = output(['lipo', '-archs', str(app / 'eBOOK')])
        if archs != 'arm64' or info['UIBackgroundModes'] != ['audio']:
            raise ValueError('Release architecture or background-mode regression')
        metadata = {'source_sha': result['source_sha'], 'archive': 'PASS_UNSIGNED_RELEASE_ARM64',
                    'architecture': archs, 'bundle_id': info['CFBundleIdentifier'], 'version': info['CFBundleShortVersionString'],
                    'app_bytes': sum(path.stat().st_size for path in app.rglob('*') if path.is_file()),
                    'model_sha256': manifest['files'][0]['sha256'], 'resource_files_verified': len(manifest['files']),
                    'signing': 'NOT_RUN', 'testflight': 'NOT_RUN', 'physical_device': 'NOT_RUN',
                    'distribution_clearance': 'INCOMPLETE', 'public_binary_artifact': False}
        (build / 's02b-device-archive.json').write_text(json.dumps(metadata, indent=2) + '\n')
        print(json.dumps(metadata), flush=True)


if __name__ == '__main__':
    main()
