#!/usr/bin/env bash
set -euo pipefail
mkdir -p build
if [[ -d /Applications/Xcode_16.4.app ]]; then
  export DEVELOPER_DIR=/Applications/Xcode_16.4.app/Contents/Developer
fi
xcodebuild -version
xcrun simctl list devices available -j > build/devices.json
SIMULATOR_ID=$(python3 - <<'PY'
import json
data = json.load(open('build/devices.json'))
for runtime, devices in sorted(data['devices'].items(), reverse=True):
    if 'iOS' in runtime:
        phone = next((d for d in devices if d.get('isAvailable') and d['name'].startswith('iPhone')), None)
        if phone:
            print(phone['udid']); break
else: raise SystemExit('No available iPhone simulator')
PY
)
export SIMULATOR_ID
xcrun simctl boot "$SIMULATOR_ID" || true
xcrun simctl bootstatus "$SIMULATOR_ID" -b
python3 - <<'PY'
import json, os, platform, subprocess
def output(*command): return subprocess.check_output(command, text=True).strip()
data = {'head_sha': output('git', 'rev-parse', 'HEAD'), 'host': platform.platform(),
        'xcode': output('xcodebuild', '-version'), 'sdk': output('xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'),
        'simulator_id': os.environ['SIMULATOR_ID'], 'runner': os.environ.get('RUNNER_OS'),
        'workflow_run': os.environ.get('GITHUB_RUN_ID')}
json.dump(data, open('build/environment.json', 'w'), indent=2)
PY
COMMON=(-project eBOOK.xcodeproj -scheme eBOOK -destination "id=$SIMULATOR_ID" -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO)
if ! xcodebuild "${COMMON[@]}" -configuration Debug build-for-testing > build/xcode-build.log 2>&1; then
  tail -100 build/xcode-build.log
  exit 1
fi
xcrun simctl install "$SIMULATOR_ID" build/DerivedData/Build/Products/Debug-iphonesimulator/eBOOK.app
APP_DATA=$(xcrun simctl get_app_container "$SIMULATOR_ID" org.example.eBOOK data)
mkdir -p "$APP_DATA/Documents"
cp .local-test-data/synthetic_long_gb18030.txt "$APP_DATA/Documents/"
cp Tests/Fixtures/synthetic.epub Tests/Fixtures/sample_utf8.txt "$APP_DATA/Documents/"
TEST_EXIT=0
xcodebuild "${COMMON[@]}" -configuration Debug test-without-building -parallel-testing-enabled NO -resultBundlePath build/Test.xcresult > build/xcode-test.log 2>&1 || TEST_EXIT=$?
xcrun xcresulttool get test-results summary --path build/Test.xcresult --format json > build/test-summary.json || true
tail -65 build/xcode-test.log
if ! xcodebuild -project eBOOK.xcodeproj -scheme eBOOK -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath build/Release CODE_SIGNING_ALLOWED=NO build > build/xcode-release.log 2>&1; then
  tail -100 build/xcode-release.log
  exit 1
fi
exit "$TEST_EXIT"
