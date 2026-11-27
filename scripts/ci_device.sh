#!/usr/bin/env bash
# No credentials, signing, vendor request, TestFlight upload or tool installation.
set -euo pipefail
mkdir -p build
major=$(xcodebuild -version | awk '/^Xcode / {split($2, parts, "."); print parts[1]}')
test "$major" -ge 26
xcodebuild -project eBOOK.xcodeproj -scheme eBOOK -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/eBOOK-device.xcarchive \
  -derivedDataPath build/DeviceDerivedData \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  CURRENT_PROJECT_VERSION="${GITHUB_RUN_NUMBER:-1}.${GITHUB_RUN_ATTEMPT:-1}" \
  archive > build/device-archive.log 2>&1 || {
    tail -100 build/device-archive.log
    exit 1
  }
python3 - <<'PY'
from pathlib import Path
import hashlib
import json
import plistlib
import subprocess
import sys
sys.path.insert(0, str(Path('scripts').resolve()))
from verify_release_bundle import validate_resources

app = Path('build/eBOOK-device.xcarchive/Products/Applications/eBOOK.app')
info = plistlib.loads((app / 'Info.plist').read_bytes())
assert info['CFBundleIdentifier'] == 'com.zhangsfish.ebook'
assert info['CFBundleShortVersionString'] == '0.1.0'
assert info['CFBundleVersion']
assert info['DTPlatformName'] == 'iphoneos'
assert info['MinimumOSVersion'] == '17.0'
assert info['ITSAppUsesNonExemptEncryption'] is False
assert info['UIBackgroundModes'] == ['audio']
assert 'UIInterfaceOrientationPortraitUpsideDown' in info['UISupportedInterfaceOrientations~ipad']
assert info['CFBundleIcons']['CFBundlePrimaryIcon']['CFBundleIconName'] == 'AppIcon'
assert (app / 'Assets.car').is_file()
assert (app / 'PrivacyInfo.xcprivacy').is_file()
assert not list(app.rglob('*.p8')) and not list(app.rglob('*.p12'))
resources = validate_resources(app)
assert not (app / 'embedded.mobileprovision').exists()
arch = subprocess.check_output(['lipo', '-archs', str(app / 'eBOOK')], text=True).strip()
assert arch == 'arm64', arch
data = {
    'head_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'xcode': subprocess.check_output(['xcodebuild', '-version'], text=True).strip(),
    'sdk': subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-version'], text=True).strip(),
    'bundle_id': info['CFBundleIdentifier'],
    'version': info['CFBundleShortVersionString'], 'build': info['CFBundleVersion'],
    'architecture': arch, 'minimum_ios': info['MinimumOSVersion'],
    'executable_sha256': hashlib.sha256((app / 'eBOOK').read_bytes()).hexdigest(),
    'archive': 'PASS_UNSIGNED_ONLY', 'signing': 'NOT_RUN',
    'testflight_upload': 'NOT_RUN', 'physical_device': 'NOT_RUN',
    'bundled_test_books': False,
}
data.update(resources)
Path('build/device-preflight.json').write_text(json.dumps(data, indent=2) + '\n')
print(json.dumps(data, indent=2))
PY
mkdir -p build/device-package/Payload
ditto build/eBOOK-device.xcarchive/Products/Applications/eBOOK.app build/device-package/Payload/eBOOK.app
ditto -c -k --keepParent build/device-package/Payload build/eBOOK-device-unsigned.ipa
python3 - <<'PY'
from pathlib import Path
import hashlib
import json

path = Path('build/device-preflight.json')
data = json.loads(path.read_text())
package = Path('build/eBOOK-device-unsigned.ipa')
data['unsigned_ipa_sha256'] = hashlib.sha256(package.read_bytes()).hexdigest()
data['unsigned_ipa_installable'] = False
path.write_text(json.dumps(data, indent=2) + '\n')
print('Unsigned device package prepared; signing is required before installation.')
PY
