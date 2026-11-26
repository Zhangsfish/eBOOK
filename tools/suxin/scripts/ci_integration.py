"""Real iOS frontend/integration checks; no host inference or signing substitute."""
from pathlib import Path
import argparse
import json
import os
import hashlib
import plistlib
import shutil
import re
import subprocess
import sys
import time
from ci_diagnostics import collect_crashes, method_coverage

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', choices=['frontend', 'integration', 'picker', 'all'], default='integration')
    args = parser.parse_args()
    build = ROOT / 'build'; build.mkdir(exist_ok=True)
    env = dict(os.environ)
    if Path('/Applications/Xcode_16.4.app').is_dir():
        env['DEVELOPER_DIR'] = '/Applications/Xcode_16.4.app/Contents/Developer'
    def output(argv):
        return subprocess.check_output(argv, cwd=ROOT, env=env, text=True).strip()
    devices = json.loads(output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))
    sdk = tuple(int(value) for value in output(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version']).split('.'))
    def version(runtime):
        return tuple(int(value) for value in re.findall(r'\d+', runtime))
    runtimes = sorted(devices['devices'].items(), key=lambda row: version(row[0]), reverse=True)
    choices = [(runtime, device) for runtime, rows in runtimes if '.iOS-' in runtime and version(runtime) <= sdk
               for device in rows if device.get('isAvailable') and device['name'].startswith('iPhone')]
    if not choices:
        raise RuntimeError('No installed iOS simulator; no installation attempted')
    runtime, device = choices[0]
    if device['state'] != 'Booted':
        subprocess.run(['xcrun', 'simctl', 'boot', device['udid']], env=env, check=True)
    with (build / 's02b-boot.log').open('w') as log:
        subprocess.run(['xcrun', 'simctl', 'bootstatus', device['udid'], '-b'], env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
    if args.scope in ['all', 'picker']:
        # Exercise the actual external-document contract. App-private/imported
        # library data is not a document provider for that same app.
        state = {'source_kind': 'original fixtures in external system LocalStorage, not reader library injection'}
        def record_provider_state():
            (build / 's02b-files-provider.json').write_text(json.dumps(state, indent=2) + '\n')
        if not device.get('dataPath') or not Path(device['dataPath']).is_dir():
            state['status'] = 'OBSERVED_SIMULATOR_DATA_PATH_UNAVAILABLE'; record_provider_state()
            raise RuntimeError('No actual Simulator data path; no group path fabricated')
        groups = Path(device['dataPath']) / 'Containers/Shared/AppGroup'
        group_ids = {}
        def scan_groups():
            for metadata in groups.glob('*/.com.apple.mobile_container_manager.metadata.plist'):
                value = plistlib.loads(metadata.read_bytes()).get('MCMMetadataIdentifier')
                if value:
                    group_ids[value] = metadata.parent
            state['observed_group_identifiers'] = sorted(group_ids)
            record_provider_state()
        def launch_files():
            try:
                launch = subprocess.run(['xcrun', 'simctl', 'launch', device['udid'], 'com.apple.DocumentsApp'],
                                        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                state['files_app_launch_exit'] = launch.returncode
            except subprocess.TimeoutExpired:
                state['files_app_launch_status'] = 'TIMEOUT_30_SECONDS'
            record_provider_state()
        scan_groups()
        if 'group.com.apple.FileProvider.LocalStorage' not in group_ids:
            launch_files()
            for attempt in range(20):
                scan_groups()
                if 'group.com.apple.FileProvider.LocalStorage' in group_ids:
                    break
                time.sleep(0.5)
        if 'group.com.apple.FileProvider.LocalStorage' not in group_ids:
            raise RuntimeError('System LocalStorage group unavailable; no external source fabricated')
        group = group_ids['group.com.apple.FileProvider.LocalStorage'].resolve()
        storage = group / 'File Provider Storage'
        state['storage_directory_preexisted'] = storage.is_dir()
        source = storage / 'eBOOK Import Test'
        if not source.resolve().is_relative_to(group):
            raise RuntimeError('External fixture directory escaped the observed system group')
        source.mkdir(parents=True, exist_ok=True)
        state['source_relative_to_group'] = 'File Provider Storage/eBOOK Import Test'
        state['files'] = []
        for name in ['sample_utf8.txt', 'synthetic.epub']:
            original = ROOT / 'Tests/Fixtures' / name
            shutil.copyfile(original, source / name)
            data = (source / name).read_bytes()
            state['files'].append({'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        record_provider_state()
        launch_files()
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
    if args.scope in ['all', 'picker']:
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
                    '-only-testing:EBookTests/SuxinStateTests', '-only-testing:EBookTests/SuxinProductionBoundaryTests']
    elif args.scope == 'picker':
        command += ['-only-testing:EBookUITests/ReaderUITests/testFilesPickerImportsSelectedTXTAndEPUB',
                    '-only-testing:EBookUITests/ReaderUITests/testSystemDocumentPickerPresentsAndCanCancel']
    try:
        code = execute(command + ['test-without-building'], 'test', 1500)
    except subprocess.TimeoutExpired:
        # Preserve partial observations as partial, never as an XCTest PASS or
        # a completed-suite count when xcodebuild did not close its result bundle.
        states = {}
        for case, state in re.findall(r"Test Case '-\[([^\]]+)\]' (started|passed|failed)",
                                      (build / 's02b-test.log').read_text()):
            states[case] = state
        timeout = {'source_sha': output(['git', 'rev-parse', 'HEAD']), 'scope': args.scope,
                   'status': 'TIMEOUT_NO_FINAL_XCTEST_SUMMARY', 'physical_device': 'NOT_RUN',
                   'observation_source': 'partial xcodebuild log, not xcresult summary',
                   'partial_log_case_states': states}
        (build / 's02b-timeout.json').write_text(json.dumps(timeout, indent=2) + '\n')
        collect_crashes(ROOT, build, device, env)
        raise
    finally:
        if args.scope in ['all', 'picker']:
            # Fixed event names/counts only: no document names, paths or text.
            with (build / 's02b-import-diagnostics.log').open('w') as log:
                try:
                    subprocess.run(['xcrun', 'simctl', 'spawn', device['udid'], 'log', 'show',
                                    '--last', '30m', '--style', 'compact', '--info',
                                    '--predicate', 'eventMessage CONTAINS "EBOOK_IMPORT"'],
                                   env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
                except subprocess.TimeoutExpired:
                    log.write('\nImport-log collection timed out; no result inferred.\n')
    raw = output(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', 'build/S02B-tests.xcresult', '--format', 'json'])
    summary = json.loads(raw)
    (build / 's02b-test-summary.json').write_text(raw + '\n')
    details = output(['xcrun', 'xcresulttool', 'get', 'test-results', 'tests', '--path', 'build/S02B-tests.xcresult', '--format', 'json'])
    (build / 's02b-test-details.json').write_text(details + '\n')
    if code:
        collect_crashes(ROOT, build, device, env)
    errors = method_coverage(ROOT, build, args.scope, summary)
    metrics = []
    for line in (build / 's02b-test.log').read_text().splitlines():
        if 'S02B_METRIC ' in line:
            metrics.append(json.loads(line.split('S02B_METRIC ', 1)[1]))
    neural = any(row.get('end_to_end_native_text') is True for row in metrics)
    result = {'source_sha': output(['git', 'rev-parse', 'HEAD']), 'scope': args.scope,
              'xcode': output(['xcodebuild', '-version']), 'simulator_runtime': runtime,
              'simulator_name': device['name'], 'host_architecture': output(['uname', '-m']),
              'host_cpu': output(['sysctl', '-n', 'machdep.cpu.brand_string']), 'host_logical_cpus': os.cpu_count(),
              'actual_counts': {key: summary[key] for key in ['totalTestCount', 'passedTests', 'failedTests', 'skippedTests']},
              'neural_audio_generation': neural, 'metrics': metrics, 'physical_device': 'NOT_RUN',
              'status': ({'frontend': 'PASS_NATIVE_FRONTEND_ONLY', 'picker': 'PASS_NATIVE_PICKER_ONLY'}.get(args.scope, 'PASS_NATIVE_INTEGRATION')) if not code else 'FAIL_ACTUAL_XCTEST'}
    (build / 's02b-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    if args.scope in ['integration', 'all'] and (not neural or len(metrics) != 2):
        errors.append('Missing actual native waveform or PCM mixer evidence')
    result['validation_errors'] = errors
    if errors: result['status'] = 'FAIL_INCOMPLETE_METHOD_OR_NEURAL_EVIDENCE'
    (build / 's02b-result.json').write_text(json.dumps(result, indent=2) + '\n')
    if args.scope in ['all', 'picker']:
        # Only this isolated simulator's original synthetic-fixture UI is
        # captured. Never export App bundles, audio or imported user books.
        with (build / 's02b-screenshots-export.log').open('w') as log:
            try:
                subprocess.run(['xcrun', 'xcresulttool', 'export', 'attachments', '--path',
                                'build/S02B-tests.xcresult', '--output-path', 'build/s02b-attachments'],
                               env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
            except subprocess.TimeoutExpired:
                log.write('\nScreenshot export timed out.\n')
        screenshots = build / 's02b-picker-screenshots'
        exported_index = build / 's02b-attachments/manifest.json'
        if exported_index.is_file() and exported_index.stat().st_size < 200_000:
            shutil.copyfile(exported_index, build / 's02b-screenshot-index.json')
        budget = 12 * 1024 * 1024
        for path in sorted((build / 's02b-attachments').rglob('*.png')):
            size = path.stat().st_size
            if size > 2 * 1024 * 1024 or size > budget:
                continue
            if not path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
                continue
            screenshots.mkdir(exist_ok=True)
            shutil.copyfile(path, screenshots / path.name)
            budget -= size
    if args.scope == 'all':
        container = Path(output(['xcrun', 'simctl', 'get_app_container', device['udid'], 'com.zhangsfish.ebook', 'data']))
        source = container / 'Documents/.s00-render-metrics-long.json'
        if not source.exists():
            raise RuntimeError('No actual long-reader regression metrics')
        shutil.copyfile(source, build / 'reader-metrics.json')
        subprocess.run([sys.executable, 'scripts/check_reader_metrics.py'], cwd=ROOT, env=env, check=True)
        shutil.copyfile(build / 'reader-metrics-summary.json', build / 's02b-reader-metrics-summary.json')
    if args.scope in ['all', 'integration'] or (args.scope == 'picker' and not code):
        archive = ['xcodebuild', '-project', 'eBOOK.xcodeproj', '-scheme', 'eBOOK', '-configuration', 'Release',
                   '-destination', 'generic/platform=iOS', '-archivePath', 'build/S02B-device.xcarchive',
                   '-derivedDataPath', 'build/S02B-DerivedData', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO', 'archive']
        legacy_entry = sdk[0] >= 26
        if legacy_entry:
            if execute(['bash', 'scripts/ci_device.sh'], 'device-entry', 900):
                raise RuntimeError('Actual original device-package entry failed')
            app = build / 'eBOOK-device.xcarchive/Products/Applications/eBOOK.app'
            shutil.copyfile(build / 'device-preflight.json', build / 's02b-legacy-device-preflight.json')
        else:
            if execute(archive, 'device-archive', 900):
                raise RuntimeError('Actual unsigned arm64 Release archive failed')
            app = build / 'S02B-device.xcarchive/Products/Applications/eBOOK.app'
        sys.path.insert(0, str(ROOT / 'scripts'))
        from verify_release_bundle import validate_resources
        resources = validate_resources(app)
        info = plistlib.loads((app / 'Info.plist').read_bytes())
        archs = output(['lipo', '-archs', str(app / 'eBOOK')])
        if archs != 'arm64' or info['UIBackgroundModes'] != ['audio']:
            raise ValueError('Release architecture or background-mode regression')
        metadata = {'source_sha': result['source_sha'], 'archive': 'PASS_UNSIGNED_RELEASE_ARM64',
                    'architecture': archs, 'bundle_id': info['CFBundleIdentifier'], 'version': info['CFBundleShortVersionString'],
                    'app_bytes': sum(path.stat().st_size for path in app.rglob('*') if path.is_file()),
                    **resources, 'original_device_entry_executed': legacy_entry,
                    'signing': 'NOT_RUN', 'testflight': 'NOT_RUN', 'physical_device': 'NOT_RUN',
                    'distribution_clearance': 'PENDING_INDEPENDENT_REVIEW', 'public_binary_artifact': False}
        (build / 's02b-device-archive.json').write_text(json.dumps(metadata, indent=2) + '\n')
        print(json.dumps(metadata), flush=True)
    if code or summary['failedTests'] or errors:
        raise RuntimeError('Actual native test failure (archive status is separate)')


if __name__ == '__main__':
    main()
