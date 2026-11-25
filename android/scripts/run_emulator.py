"""Actual Android emulator + native instrumentation, isolated free CI only.
Uses installed SDK manager. Does not auto-accept any additional license prompt.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'android/build'
OUT = BUILD / 'emulator'
OUT.mkdir(parents=True, exist_ok=True)
SDK = Path(os.environ['ANDROID_HOME'])
JAVA = Path(os.environ['JAVA_HOME']) / 'bin'
TOOLS = SDK / 'build-tools/35.0.0'
ADB = SDK / 'platform-tools/adb'
API = int(os.environ.get('EMULATOR_API', '30'))
IMAGE = 'system-images;android-30;default;x86_64' if API == 30 else 'system-images;android-35;google_apis;x86_64'
AVD = 'ebook-reader-' + str(API)


def run(args, **kwargs):
    print('+', ' '.join(str(x) for x in args), flush=True)
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def adb(*args, **kwargs):
    return run([ADB, *args], **kwargs)


def main():
    os.environ['PATH'] = str(JAVA) + os.pathsep + os.environ['PATH']
    manager = SDK / 'cmdline-tools/latest/bin/sdkmanager'
    avdmanager = SDK / 'cmdline-tools/latest/bin/avdmanager'
    run([manager, '--install', IMAGE], stdin=subprocess.DEVNULL)
    run([avdmanager, 'create', 'avd', '--force', '--name', AVD, '--package', IMAGE, '--device', 'pixel_2'], input='no\n', text=True)
    key = BUILD / 'ephemeral-ci-only.jks'
    os.environ['EBOOK_CI_KEY_PASS'] = secrets.token_hex(20)
    run([JAVA / 'keytool', '-genkeypair', '-keystore', key, '-storepass:env', 'EBOOK_CI_KEY_PASS', '-keypass:env', 'EBOOK_CI_KEY_PASS',
         '-alias', 'ci', '-dname', 'CN=eBOOK temporary emulator test', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '2', '-noprompt'])
    for name in ('ebook', 'tests'):
        run([TOOLS / 'apksigner', 'sign', '--ks', key, '--ks-pass', 'env:EBOOK_CI_KEY_PASS', '--ks-key-alias', 'ci',
             '--out', BUILD / (name + '-ci.apk'), BUILD / (name + '-unsigned.apk')])
    with (OUT / 'test-signature.txt').open('w') as result:
        run([TOOLS / 'apksigner', 'verify', '--verbose', '--print-certs', BUILD / 'ebook-ci.apk'], stdout=result)
    with (OUT / 'package.txt').open('w') as result:
        run([TOOLS / 'aapt2', 'dump', 'badging', BUILD / 'ebook-ci.apk'], stdout=result)
    key.unlink(missing_ok=True)
    emulator_log = (OUT / 'emulator.log').open('w')
    process = subprocess.Popen([str(SDK / 'emulator/emulator'), '-avd', AVD, '-no-window', '-no-audio', '-no-boot-anim',
                                '-no-snapshot', '-gpu', 'swiftshader', '-memory', '3072', '-cores', '2'], stdout=emulator_log, stderr=subprocess.STDOUT)
    try:
        adb('wait-for-device', timeout=180)
        until = time.monotonic() + 240
        while time.monotonic() < until:
            if process.poll() is not None:
                raise RuntimeError('Emulator exited before boot')
            value = subprocess.check_output([str(ADB), 'shell', 'getprop', 'sys.boot_completed'], text=True).strip()
            if value == '1':
                break
            time.sleep(2)
        else:
            raise RuntimeError('Emulator did not finish booting')
        for setting in ('window_animation_scale', 'transition_animation_scale', 'animator_duration_scale'):
            adb('shell', 'settings', 'put', 'global', setting, '0')
        adb('shell', 'input', 'keyevent', '82')
        adb('install', '-t', str(BUILD / 'ebook-ci.apk'))
        adb('install', '-t', str(BUILD / 'tests-ci.apk'))
        if API >= 33:
            adb('shell', 'pm', 'grant', 'cn.zhangsfish.ebook', 'android.permission.POST_NOTIFICATIONS')
        failures = []
        for phase in ('main', 'resume'):
            if phase == 'resume':
                adb('shell', 'am', 'force-stop', 'cn.zhangsfish.ebook')
            response = subprocess.run([str(ADB), 'shell', 'am', 'instrument', '-w', '-r', '-e', 'phase', phase,
                                       'cn.zhangsfish.ebook.tests/.ReaderInstrumentation'], capture_output=True, text=True, timeout=700)
            (OUT / ('instrumentation-' + phase + '.txt')).write_text(response.stdout + response.stderr, encoding='utf-8')
            print(response.stdout, flush=True)
            adb('pull', '/sdcard/Android/data/cn.zhangsfish.ebook/files/evidence/.', str(OUT))
            report = json.loads((OUT / ('results-' + phase + '.json')).read_text('utf-8'))
            if report['failed'] or report['passed'] == 0:
                failures.append(phase)
        report = dict(api=API, image=IMAGE, physical_device=False, system_tts_voice_test='controlled test-only PCM engine, not Huawei installed voice',
                      package_install='PASS', phases_failed=failures)
        (OUT / 'emulator-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        if failures:
            raise RuntimeError('Native instrumentation failures: ' + ', '.join(failures))
    finally:
        subprocess.run([str(ADB), 'logcat', '-d', '-v', 'threadtime'], stdout=(OUT / 'logcat.txt').open('w'), check=False)
        subprocess.run([str(ADB), 'shell', 'dumpsys', 'meminfo', 'cn.zhangsfish.ebook'], stdout=(OUT / 'memory.txt').open('w'), check=False)
        subprocess.run([str(ADB), 'emu', 'kill'], stdout=subprocess.DEVNULL, check=False)
        if process.poll() is None:
            process.terminate()
        emulator_log.close()


if __name__ == '__main__':
    main()
