"""Inspect a hash-pinned iOS XCFramework as data, never install/execute it.

Distinguish original ZIP notices from hash-pinned, matching-source supplements.
No neural model or waveform is included in the resulting small JSON evidence.
"""
from pathlib import Path
import argparse
import hashlib
import json
import plistlib
import re
import shutil
import subprocess
import urllib.request
import urllib.error
import zipfile

ROOT = Path(__file__).resolve().parents[3]
URL = 'https://github.com/csukuangfj/onnxruntime-libs/releases/download/v1.28.2/onnxruntime-ios-static-xcframework-1.28.2.xcframework.zip'
SHA = '2c2299acbb461d26d4bac4bc85985d40e7c7177ed6072703ae0846d88b0b4599'
SOURCE_COMMIT = '33ca9628233dc8f002435e868d4c2e9f82766ca1'
SOURCE_NOTICES = [
    ('LICENSE', 'ONNXRuntime-LICENSE.txt', 1073,
     '2f07c72751aed99790b8a4869cf2311df85a860b22ded05fa22803587a48922c'),
    ('ThirdPartyNotices.txt', 'ONNXRuntime-ThirdPartyNotices.txt', 325054,
     '0e07b95f3a8d6230037707c5c4a2b554d12c4cb67369669ac255635528ffcee2'),
]


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
        binaries = []
        for name in members:
            if not name.endswith('/onnxruntime.framework/onnxruntime'):
                continue
            data = package.read(name)
            stamps = sorted({stamp.decode('ascii') for stamp in re.findall(rb'ORT Build Info: [ -~]+', data)})
            if not stamps or any('git-commit-id=' + SOURCE_COMMIT[:7] + ',' not in stamp for stamp in stamps):
                raise ValueError('Runtime embedded source commit does not match notice source')
            binaries.append({'member': name, 'sha256': hashlib.sha256(data).hexdigest(),
                             'bytes': len(data), 'embedded_build_info': stamps})
    supplemental = []
    source_cache = local / 'downloads/source-notices'; source_cache.mkdir(parents=True, exist_ok=True)
    for path, bundle_file, size, sha in SOURCE_NOTICES:
        url = f'https://raw.githubusercontent.com/csukuangfj/onnxruntime/{SOURCE_COMMIT}/{path}'
        cached = source_cache / (SOURCE_COMMIT[:7] + '-' + bundle_file)
        if cached.exists():
            data = cached.read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read(size + 1)
        if len(data) != size or hashlib.sha256(data).hexdigest() != sha:
            raise ValueError('Exact-commit source notice integrity mismatch')
        if not cached.exists():
            cached.write_bytes(data)
        (notices / bundle_file).write_bytes(data)
        supplemental.append({'source_url': url, 'source_repository': 'csukuangfj/onnxruntime',
                             'source_commit': SOURCE_COMMIT, 'bundle_file': bundle_file,
                             'bytes': size, 'sha256': sha, 'embedded_short_commit_matches': True,
                             'reproducible_build_verified': False})
    evidence = {'runtime_version': '1.28.2', 'spm_revision': '8ebc5ebf92190903c274a7621ba4c96a732335ec',
                'archive_url': URL, 'archive_sha256': SHA, 'archive_bytes': archive.stat().st_size,
                'available_libraries': info['AvailableLibraries'], 'binaries': binaries, 'included_notices': included,
                'supplemental_source_notices': supplemental,
                'distribution_clearance': 'PENDING_INDEPENDENT_REVIEW',
                'notice_limits': 'Exact embedded commit located in binary publisher fork; not a reproducible-build proof or complete static dependency BOM/model-rights determination.'}
    queries = []
    for url in ['https://api.github.com/repos/microsoft/onnxruntime/git/ref/tags/v1.28.2',
                'https://raw.githubusercontent.com/microsoft/onnxruntime/v1.28.2/LICENSE',
                'https://raw.githubusercontent.com/microsoft/onnxruntime/v1.28.2/ThirdPartyNotices.txt']:
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                data = response.read(2 * 1024 * 1024)
                queries.append({'url': url, 'http_status': response.status, 'bytes': len(data),
                                'sha256': hashlib.sha256(data).hexdigest(), 'binary_binding_verified': False})
        except urllib.error.HTTPError as problem:
            queries.append({'url': url, 'http_status': problem.code})
        except (OSError, TimeoutError):
            queries.append({'url': url, 'http_status': None, 'state': 'NETWORK_UNAVAILABLE_NOT_LICENSE_VERDICT'})
    evidence['source_notice_queries'] = queries
    if args.verify_spm_dir:
        resolved = []
        # SPM may resolve unused static AND shared products from this package.
        # Inspect the exact binary target in Xcode's ProcessXCFramework command,
        # not all unrelated frameworks sharing the leaf name onnxruntime.
        target = args.verify_spm_dir / 'artifacts/onnxruntime-libs/OnnxruntimeIOS'
        for item in binaries:
            binary = target / item['member']
            actual = digest(binary) if binary.is_file() else None
            if actual != item['sha256']:
                details = {'member': item['member'], 'expected_sha256': item['sha256'], 'actual_sha256': actual,
                           'target_exists': target.is_dir(), 'state': 'FAIL_RESOLVED_RUNTIME_INTEGRITY'}
                build = ROOT / 'build'; build.mkdir(exist_ok=True)
                (build / 's02b-runtime-verification-failed.json').write_text(json.dumps(details, indent=2) + '\n')
                print(json.dumps(details), flush=True)
                raise ValueError('Resolved Xcode runtime differs from pinned XCFramework')
            archs = subprocess.check_output(['lipo', '-archs', str(binary)], text=True).strip()
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
                      'included_notice_count': len(included), 'supplemental_notice_count': len(supplemental),
                      'embedded_source_commit_prefix': SOURCE_COMMIT[:7], 'slices': len(info['AvailableLibraries'])}))


if __name__ == '__main__':
    main()
