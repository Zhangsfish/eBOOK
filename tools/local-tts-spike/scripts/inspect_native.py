"""Read exact pinned XCFramework archives; never installs or executes their code."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import platform
import plistlib
import shutil
import subprocess
import time
import urllib.request
import uuid
import zipfile
from assets import SPIKE, REPO, sha256


def download(url, expected, directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (expected + '.zip')
    if path.exists():
        if sha256(path) != expected:
            raise ValueError('Existing archive mismatch; preserve it for inspection')
        return path
    for attempt in range(3):
        partial = directory / (uuid.uuid4().hex + '.part')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'eBOOK-S02A1-artifact-audit'})
            with urllib.request.urlopen(request, timeout=90) as incoming, partial.open('xb') as output:
                shutil.copyfileobj(incoming, output, 1024 * 1024)
            if sha256(partial) != expected:
                raise ValueError('Pinned native archive SHA256 mismatch')
            partial.rename(path)
            return path
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1)


def inspect_archive(path, directory):
    with zipfile.ZipFile(path) as source:
        members = source.infolist()
        if len(members) > 20000 or sum(m.file_size for m in members) > 4 * 1024**3:
            raise ValueError('Unexpected native archive size')
        for item in members:
            relative = PurePosixPath(item.filename)
            if relative.is_absolute() or '..' in relative.parts or '\\' in item.filename:
                raise ValueError('Unsafe native archive member')
        infos = [m for m in members if m.filename.endswith('.xcframework/Info.plist') and '__MACOSX' not in m.filename]
        if len(infos) != 1:
            raise ValueError('Expected one top-level XCFramework Info.plist')
        info = plistlib.loads(source.read(infos[0]))
        prefix = infos[0].filename.rsplit('/', 1)[0]
        libraries = []
        for library in info['AvailableLibraries']:
            entry = dict(library)
            folder = prefix + '/' + library['LibraryIdentifier'] + '/'
            binary = folder + library['LibraryPath']
            if binary.endswith('.framework'):
                binary += '/' + PurePosixPath(binary).stem
            if binary not in source.namelist():
                raise ValueError('Declared library binary missing: ' + binary)
            digest = hashlib.sha256()
            with source.open(binary) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            entry.update(binary_member=binary, binary_bytes=source.getinfo(binary).file_size,
                         binary_sha256=digest.hexdigest())
            if platform.system() == 'Darwin':
                native = directory / (digest.hexdigest() + '.library')
                if not native.exists():
                    with source.open(binary) as incoming, native.open('xb') as outgoing:
                        shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
                result = subprocess.run(['xcrun', 'lipo', '-info', str(native)], capture_output=True, text=True)
                entry['actual_lipo_exit'] = result.returncode
                entry['actual_lipo_output'] = (result.stdout + result.stderr).replace(str(native), '<VERIFIED_LIBRARY>').strip()
            else:
                entry['actual_lipo_status'] = 'NOT_RUN_NON_MACOS_HOST'
            libraries.append(entry)
        notices = []
        header_notices = []
        for member in members:
            name = member.filename.lower()
            if not member.is_dir() and any(word in name for word in ['license', 'copying', 'notice', 'thirdparty']):
                raw = source.read(member)
                notices.append({'path': member.filename, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'text_preview': raw[:4000].decode('utf-8', errors='replace') if len(raw) < 2 * 1024**2 else 'TOO_LARGE_FOR_PREVIEW'})
            if member.filename.endswith(('/c-api.h', '/onnxruntime_c_api.h')):
                raw = source.read(member)
                lines = raw.decode('utf-8', errors='replace').splitlines()[:35]
                header_notices.append({'path': member.filename, 'sha256': hashlib.sha256(raw).hexdigest(),
                    'notice_lines': [line for line in lines if any(word in line.lower() for word in ['copyright', 'licensed', 'license.'])]})
        return {'archive_sha256': sha256(path), 'archive_bytes': path.stat().st_size,
                'archive_members': len(members), 'info_plist_sha256': hashlib.sha256(source.read(infos[0])).hexdigest(),
                'libraries': libraries, 'notices': notices, 'header_notice_references': header_notices,
                'notice_status': 'FILES_INSPECTED_NOT_LEGAL_CLEARANCE' if notices else 'NO_NOTICE_FILES_IN_ARCHIVE'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=REPO / '.local-test-data/s02a1/native')
    parser.add_argument('--output', type=Path, default=REPO / '.local-test-data/s02a1/native-audit.json')
    parser.add_argument('--require-simulator-arch')
    args = parser.parse_args()
    local = (REPO / '.local-test-data').resolve()
    if not args.directory.resolve().is_relative_to(local) or not args.output.resolve().is_relative_to(local):
        raise ValueError('Native downloads and diagnostics must remain ignored')
    pins = json.loads((SPIKE / 'manifests/native-runtime.json').read_text(encoding='utf-8'))
    result = {'status': 'RUNNING', 'host_system': platform.system(), 'host_architecture': platform.machine(),
              'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
              'components': {}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        for name in ['sherpa', 'onnxruntime']:
            pin = pins[name]['ios_binary']
            archive = download(pin['url'], pin['sha256'], args.directory)
            result['components'][name] = inspect_archive(archive, args.directory)
            result['components'][name]['source_url'] = pin['url']
            print('S02A1_NATIVE_VERIFIED', name, archive.stat().st_size, flush=True)
        if args.require_simulator_arch:
            for name, component in result['components'].items():
                matches = [r for r in component['libraries'] if r.get('SupportedPlatform') == 'ios'
                    and r.get('SupportedPlatformVariant') == 'simulator'
                    and args.require_simulator_arch in r['SupportedArchitectures']]
                if not matches:
                    result.update(status='BLOCKED_ARCHITECTURE', reason=name + ' lacks requested simulator architecture')
                    return 3
                if platform.system() == 'Darwin' and not any(r.get('actual_lipo_exit') == 0 and
                        args.require_simulator_arch in r.get('actual_lipo_output', '') for r in matches):
                    result.update(status='BLOCKED_ARCHITECTURE', reason=name + ' actual lipo result does not confirm required slice')
                    return 3
        result['status'] = 'PASS_PINNED_ARCHIVES_INSPECTED'
        return 0
    except Exception as error:
        result.update(status='BLOCKED_NATIVE_ARTIFACT', reason=type(error).__name__ + ': ' + str(error)[:500])
        raise
    finally:
        args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
