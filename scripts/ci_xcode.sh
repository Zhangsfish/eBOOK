#!/usr/bin/env bash
set -euo pipefail
mkdir -p build
if [[ -z "${DEVELOPER_DIR:-}" && -d /Applications/Xcode_16.4.app ]]; then
  export DEVELOPER_DIR=/Applications/Xcode_16.4.app/Contents/Developer
fi
xcodebuild -version
xcrun --sdk iphonesimulator --show-sdk-version > build/sdk-version.txt
xcrun simctl list devices available -j > build/devices.json
SIMULATOR_ID=$(python3 - <<'PY'
import json, re
data = json.load(open('build/devices.json'))
sdk = tuple(int(v) for v in open('build/sdk-version.txt').read().strip().split('.'))
def version(runtime): return tuple(int(v) for v in re.findall(r'\d+', runtime))
for runtime, devices in sorted(data['devices'].items(), key=lambda item: version(item[0]), reverse=True):
    if version(runtime) > sdk: continue
    if 'iOS' in runtime:
        phone = next((d for d in devices if d.get('isAvailable') and d['name'].startswith('iPhone')), None)
        if phone:
            print(phone['udid']); break
else: raise SystemExit('No available iPhone simulator')
PY
)
export SIMULATOR_ID
python3 - <<'PY'
import json, os, platform, subprocess
def output(*command): return subprocess.check_output(command, text=True).strip()
data = {'head_sha': output('git', 'rev-parse', 'HEAD'), 'host': platform.platform(),
        'xcode': output('xcodebuild', '-version'), 'sdk': output('xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'),
        'simulator_id': os.environ['SIMULATOR_ID'], 'runner': os.environ.get('RUNNER_OS'),
        'workflow_run': os.environ.get('GITHUB_RUN_ID')}
json.dump(data, open('build/environment.json', 'w'), indent=2)
PY
xcrun simctl boot "$SIMULATOR_ID" || true
python3 - <<'PY'
import os, subprocess
from pathlib import Path

log_path = Path('build/simulator-boot.log')
timeout = int(os.environ.get('SIMULATOR_BOOT_TIMEOUT_SECONDS', '300'))
print(f'Waiting up to {timeout} seconds for initial simulator migration', flush=True)
with log_path.open('w') as log:
    try:
        subprocess.run(['xcrun', 'simctl', 'bootstatus', os.environ['SIMULATOR_ID'], '-b'],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=timeout)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        print('\n'.join(log_path.read_text().splitlines()[-25:]), flush=True)
        raise
print('Simulator boot completed', flush=True)
PY
COMMON=(-project eBOOK.xcodeproj -scheme eBOOK -destination "id=$SIMULATOR_ID" -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO)
echo 'Starting Debug build-for-testing'
if ! xcodebuild "${COMMON[@]}" -configuration Debug build-for-testing > build/xcode-build.log 2>&1; then
  tail -100 build/xcode-build.log
  exit 1
fi
xcrun simctl install "$SIMULATOR_ID" build/DerivedData/Build/Products/Debug-iphonesimulator/eBOOK.app
APP_DATA=$(xcrun simctl get_app_container "$SIMULATOR_ID" com.zhangsfish.ebook data)
mkdir -p "$APP_DATA/Documents"
cp .local-test-data/synthetic_long_gb18030.txt "$APP_DATA/Documents/"
cp Tests/Fixtures/synthetic.epub Tests/Fixtures/sample_utf8.txt "$APP_DATA/Documents/"
TEST_EXIT=0
echo 'Starting simulator unit and UI tests'
xcodebuild "${COMMON[@]}" -configuration Debug test-without-building -parallel-testing-enabled NO -resultBundlePath build/Test.xcresult > build/xcode-test.log 2>&1 || TEST_EXIT=$?
xcrun xcresulttool get test-results summary --path build/Test.xcresult --format json > build/test-summary.json || true
xcrun xcresulttool get test-results tests --path build/Test.xcresult --format json > build/test-details.json || true
xcrun xcresulttool export attachments --path build/Test.xcresult --output-path build/attachments > build/attachments-export.log 2>&1 || true
python3 - <<'PY'
from pathlib import Path
import shutil
output = Path('build/screenshots')
for source in Path('build/attachments').rglob('*.png'):
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output / source.name)
PY
APP_DATA=$(xcrun simctl get_app_container "$SIMULATOR_ID" com.zhangsfish.ebook data)
if [[ -f "$APP_DATA/Documents/.s00-render-metrics-long.json" ]]; then
  cp "$APP_DATA/Documents/.s00-render-metrics-long.json" build/reader-metrics.json
fi
if [[ "$TEST_EXIT" -eq 0 ]]; then
  python3 scripts/check_reader_metrics.py
fi
tail -65 build/xcode-test.log
echo 'Starting Release simulator build'
if ! xcodebuild -project eBOOK.xcodeproj -scheme eBOOK -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath build/Release CODE_SIGNING_ALLOWED=NO build > build/xcode-release.log 2>&1; then
  tail -100 build/xcode-release.log
  exit 1
fi
exit "$TEST_EXIT"
