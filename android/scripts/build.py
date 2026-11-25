"""Compile with an existing official SDK/JDK only; no Gradle/dependency installs.
Produces unsigned aligned APKs. Upgrade signing is a separate LOCAL-only step.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ANDROID = Path(__file__).resolve().parents[1]
ROOT = ANDROID.parent
BUILD = ANDROID / 'build'


def run(args, **kwargs):
    print('+', ' '.join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], check=True, cwd=ROOT, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk', default=os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT'))
    parser.add_argument('--jdk', default=os.environ.get('JAVA_HOME'))
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--core-only', action='store_true')
    parser.add_argument('--instrumentation', action='store_true')
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    java = Path(args.jdk) / 'bin' if args.jdk else Path('')
    suffix = '.exe' if os.name == 'nt' else ''
    javac = java / ('javac' + suffix) if args.jdk else 'javac'
    java_exe = java / ('java' + suffix) if args.jdk else 'java'
    jar = java / ('jar' + suffix) if args.jdk else 'jar'
    if args.jdk:
        os.environ['JAVA_HOME'] = args.jdk
        os.environ['PATH'] = str(java) + os.pathsep + os.environ['PATH']
    if args.test or args.core_only:
        core = BUILD / 'core'
        core.mkdir(exist_ok=True)
        run([javac, '-encoding', 'UTF-8', '--release', '8', '-Xlint:-options', '-d', core,
             *sorted((ANDROID / 'app/src/main/java/cn/zhangsfish/ebook/core').glob('*.java')), ANDROID / 'tests/CoreTests.java'])
        fixture = ROOT / '.local-test-data/android-fixtures/original_long_gb18030.txt'
        if not fixture.exists():
            run([sys.executable, ROOT / 'scripts/generate_long_gb18030_fixture.py', '--output', fixture])
        run([java_exe, '-Xmx256m', '-cp', core, 'CoreTests', ROOT, BUILD / 'core-evidence'])
    if args.core_only:
        return
    if not args.sdk:
        raise SystemExit('Existing Android SDK required (--sdk); this script never installs it.')
    sdk = Path(args.sdk)
    platform = sdk / 'platforms/android-35/android.jar'
    tool = sdk / 'build-tools/35.0.0'
    if not platform.exists() or not tool.exists():
        raise SystemExit('Preinstalled SDK platform35 / build-tools35.0.0 required.')
    aapt = tool / ('aapt2' + suffix)
    dex = tool / ('d8.bat' if os.name == 'nt' else 'd8')
    # The platform hides LambdaMetafactory. Official SDK compiler stubs allow
    # javac to emit Java8 call sites, then official D8 desugars them for Android.
    boot = os.pathsep.join([str(platform), str(tool / 'core-lambda-stubs.jar')])
    compiled = BUILD / 'compiled-res.zip'
    generated = BUILD / 'generated'
    generated.mkdir(exist_ok=True)
    run([aapt, 'compile', '--dir', ANDROID / 'app/src/main/res', '-o', compiled])
    base = BUILD / 'base.apk'
    run([aapt, 'link', '-I', platform, '--manifest', ANDROID / 'app/src/main/AndroidManifest.xml',
         '--java', generated, '-o', base, compiled])
    classes = BUILD / 'classes'
    classes.mkdir(exist_ok=True)
    sources = sorted((ANDROID / 'app/src/main/java').rglob('*.java')) + sorted(generated.rglob('*.java'))
    run([javac, '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-Xlint:-options', '-bootclasspath', boot, '-d', classes, *sources])
    app_jar = BUILD / 'app-classes.jar'
    run([jar, 'cf', app_jar, '-C', classes, '.'])

    def apk(name, resource_apk, class_jar, classpath=None):
        dex_dir = BUILD / (name + '-dex')
        dex_dir.mkdir(exist_ok=True)
        command = [dex, '--lib', platform, '--min-api', '26', '--output', dex_dir]
        if classpath:
            command += ['--classpath', classpath]
        run([*command, class_jar])
        unsigned = BUILD / (name + '-unaligned.apk')
        shutil.copy2(resource_apk, unsigned)
        with zipfile.ZipFile(unsigned, 'a', zipfile.ZIP_DEFLATED) as archive:
            for file in dex_dir.glob('*.dex'):
                archive.write(file, file.name)
        result = BUILD / (name + '-unsigned.apk')
        run([tool / ('zipalign' + suffix), '-f', '4', unsigned, result])
        return result

    apk('ebook', base, app_jar)
    if args.instrumentation:
        assets = BUILD / 'test-assets'
        assets.mkdir(exist_ok=True)
        for source in (ROOT / 'Tests/Fixtures').iterdir():
            if source.suffix in ('.txt', '.epub'):
                shutil.copy2(source, assets / source.name)
        shutil.copy2(ROOT / '.local-test-data/android-fixtures/original_long_gb18030.txt', assets / 'original_long_gb18030.txt')
        test_base = BUILD / 'test-base.apk'
        run([aapt, 'link', '-I', platform, '--manifest', ANDROID / 'tests/instrumentation/AndroidManifest.xml', '-A', assets, '-o', test_base])
        test_classes = BUILD / 'test-classes'
        test_classes.mkdir(exist_ok=True)
        run([javac, '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-Xlint:-options', '-bootclasspath', boot,
             '-cp', app_jar, '-d', test_classes, *sorted((ANDROID / 'tests/instrumentation').glob('*.java'))])
        test_jar = BUILD / 'test-classes.jar'
        run([jar, 'cf', test_jar, '-C', test_classes, '.'])
        apk('tests', test_base, test_jar, app_jar)
    source_manifest = ROOT / 'SOURCE.json'
    if source_manifest.exists():
        provenance = json.loads(source_manifest.read_text('utf-8'))
        for name, expected in provenance['files'].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise ValueError('Deployed source digest changed: ' + name)
        sha, dirty = provenance['source_sha'], False
    else:
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))
    info = dict(source_sha=sha, source_dirty=dirty,
                sdk_platform=35, build_tools='35.0.0', min_sdk=26, target_sdk=35,
                version_name='0.1.0-android.1', version_code=1, runtime_dependencies=[], signed=False)
    (BUILD / 'build-info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
