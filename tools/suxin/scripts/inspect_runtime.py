"""Inspect a hash-pinned iOS XCFramework as data, never install/execute it.

Extract only included third-party notices; preserve honest missing-notice state.
No neural model or waveform is included in the resulting small JSON evidence.
"""
from pathlib import Path
import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[3]
URL = 'https://github.com/csukuangfj/onnxruntime-libs/releases/download/v1.28.2/onnxruntime-ios-static-xcframework-1.28.2.xcframework.zip'
SHA = '2c2299acbb461d26d4bac4bc85985d40e7c7177ed6072703ae0846d88b0b4599'


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--verify-spm-dir', type=Path)
    args = parser.parse_args()
    local = ROOT / '.local-test-data/s02b'
    archive = args.archive or local / 'downloads/onnxruntime-ios-1.28.2.zip'
    if not archive.exists():
        if args.archive:
            raise FileNotFoundError('Specified local archive does not exist')
        archive.parent.mkdir(parents=True, exist_ok=True)
        part = archive.with_suffix('.partial')
        with urllib.request.urlopen(URL, timeout=90) as response, part.open('xb') as output:
            total = 0
            while data := response.read(1024 * 1024):
                total += len(data)
                if total > 256 * 1024 * 1024:
                    raise ValueError('Unexpected runtime archive size')
                output.write(data)
        if digest(part) != SHA:
            raise ValueError('Runtime checksum mismatch; preserve partial for inspection')
        part.rename(archive)
    if digest(archive) != SHA:
        raise ValueError('Runtime checksum mismatch; existing file preserved')
    notices = local / 'bundle/NativeNotices'; notices.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        members = package.namelist()
        plist_name = next(name for name in members if name.endswith('.xcframework/Info.plist'))
        info = plistlib.loads(package.read(plist_name))
        included = []
        for name in members:
            leaf = Path(name).name
            if leaf.lower() in ['license', 'license.txt', 'thirdpartynotices.txt', 'third_party_notices.txt', 'notice', 'notice.txt']:
                data = package.read(name)
                if len(data) > 2 * 1024 * 1024:
                    raise ValueError('Unexpected notice size')
                output_name = hashlib.sha256(name.encode()).hexdigest()[:10] + '-' + leaf
                (notices / output_name).write_bytes(data)
                included.append({'member': name, 'bundle_file': output_name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        binaries = [{'member': name, 'sha256': hashlib.sha256(package.read(name)).hexdigest(), 'bytes': package.getinfo(name).file_size}
                    for name in members if name.endswith('/onnxruntime.framework/onnxruntime')]
    evidence = {'runtime_version': '1.28.2', 'spm_revision': '8ebc5ebf92190903c274a7621ba4c96a732335ec',
                'archive_url': URL, 'archive_sha256': SHA, 'archive_bytes': archive.stat().st_size,
                'available_libraries': info['AvailableLibraries'], 'binaries': binaries, 'included_notices': included,
                'distribution_clearance': 'INCOMPLETE_REQUIRES_FULL_TRANSITIVE_REVIEW'}
    if args.verify_spm_dir:
        resolved = []
        for item in binaries:
            matches = [path for path in args.verify_spm_dir.rglob('onnxruntime')
                       if path.as_posix().endswith(item['member'])]
            if len(matches) != 1 or digest(matches[0]) != item['sha256']:
                raise ValueError('Resolved Xcode runtime differs from pinned XCFramework')
            archs = subprocess.check_output(['lipo', '-archs', str(matches[0])], text=True).strip()
            resolved.append({'member': item['member'], 'actual_architectures': archs, 'sha256': item['sha256']})
        if len(resolved) != 2:
            raise ValueError('Both device and simulator slices must be inspected')
        evidence['resolved_xcode_slices'] = resolved
    shutil.copyfile(ROOT / 'tools/suxin/NOTICE.md', notices / 'Integration-NOTICE.md')
    text = json.dumps(evidence, indent=2, ensure_ascii=False) + '\n'
    (notices / 'runtime-provenance.json').write_text(text, encoding='utf-8', newline='\n')
    build = ROOT / 'build'; build.mkdir(exist_ok=True)
    (build / 's02b-runtime.json').write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps({'runtime_archive_sha256': SHA, 'runtime_archive_bytes': archive.stat().st_size,
                      'included_notice_count': len(included), 'slices': len(info['AvailableLibraries'])}))


if __name__ == '__main__':
    main()
