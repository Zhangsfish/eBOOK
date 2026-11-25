"""Owner-authorized, project-only wheel resolution/audit, then offline installation.

Run resolve first and inspect the resulting wheel metadata before running install.
Only binary PyPI wheels are accepted; model/source code is never installed here.
"""
from pathlib import Path
import argparse
import email
import hashlib
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import urllib.error
import venv
import zipfile

REPO = Path(__file__).resolve().parents[4]
LOCAL = REPO / '.local-test-data/s02a2/s02a3'
RUNTIME = LOCAL / 'runtime'
PINS = ['numpy==1.26.4', 'onnxruntime==1.20.1', 'pypinyin==0.55.0',
        'piper-tts==1.8.0', 'pathvalidate==3.3.1']


def fetch_json(url):
    return json.loads(fetch_bytes(url))


def fetch_bytes(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read(80_000_001)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            print('Retrying interrupted official download', flush=True)


def python_path():
    return RUNTIME / 'venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')


def pip(*args):
    subprocess.run([str(python_path()), '-m', 'pip', '--isolated',
                    '--disable-pip-version-check', *args], check=True)


def resolve():
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError('Use the existing Python3.11 interpreter')
    if not RUNTIME.exists():
        RUNTIME.mkdir(parents=True, exist_ok=False)
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(RUNTIME / 'venv')
    config = (RUNTIME / 'venv/pyvenv.cfg').read_text(encoding='utf-8').lower()
    assert 'include-system-site-packages = false' in config
    if not (RUNTIME / 'resolution.json').exists():
        pip('install', '--dry-run', '--ignore-installed', '--only-binary=:all:',
            '--index-url', 'https://pypi.org/simple', '--no-input',
            '--report', str(RUNTIME / 'resolution.json'), *PINS)
    resolution = json.loads((RUNTIME / 'resolution.json').read_text(encoding='utf-8'))
    proposal = json.loads((REPO / 'tools/local-tts-spike/s02a2/manifests/suxin-frontend-proposal.json').read_text(encoding='utf-8'))
    vetted = {row['filename']: row for row in proposal['packages']}
    wheelhouse = RUNTIME / 'wheels'; wheelhouse.mkdir(exist_ok=True)
    rows = []
    for package in resolution['install']:
        meta = package['metadata']; name, version = meta['name'], meta['version']
        url = package['download_info']['url']
        parsed = urllib.parse.urlparse(url)
        filename = Path(urllib.parse.unquote(parsed.path)).name
        if parsed.scheme != 'https' or parsed.hostname != 'files.pythonhosted.org' or not filename.endswith('.whl'):
            raise ValueError('Only official binary PyPI distributions are allowed')
        official = fetch_json('https://pypi.org/pypi/' + name + '/' + version + '/json')
        match = [item for item in official['urls'] if item['filename'] == filename and item['url'] == url]
        if len(match) != 1:
            raise ValueError('Wheel missing from versioned official metadata')
        item = match[0]; expected = item['digests']['sha256']
        if expected != package['download_info']['archive_info']['hashes']['sha256']:
            raise ValueError('Resolver and official digest disagree')
        if filename in vetted and (expected != vetted[filename]['sha256'] or item['size'] != vetted[filename]['bytes']):
            raise ValueError('Previously vetted frontend wheel changed')
        path = wheelhouse / filename
        data = path.read_bytes() if path.exists() else fetch_bytes(url)
        if len(data) != item['size'] or len(data) > 80_000_000 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Wheel byte/hash mismatch')
        if not path.exists():
            path.write_bytes(data)
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError('Corrupt wheel')
            metadata_names = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
            metadata = email.message_from_bytes(archive.read(metadata_names[0]))
            license_files = [n for n in archive.namelist() if any(word in Path(n).name.lower() for word in ['license', 'copying', 'notice'])]
        row = {'name': name, 'version': version, 'filename': filename, 'bytes': len(data),
               'sha256': expected, 'source': 'https://pypi.org/pypi/' + name + '/' + version + '/json',
               'license_expression': metadata.get('License-Expression'), 'license': metadata.get('License'),
               'license_classifiers': [c for c in metadata.get_all('Classifier', []) if c.startswith('License')],
               'requires_dist': metadata.get_all('Requires-Dist', []), 'license_files': license_files}
        rows.append(row)
        print('AUDITED_WHEEL', name, version, len(data), flush=True)
    lines = [row['name'] + '==' + row['version'] + ' --hash=sha256:' + row['sha256'] for row in rows]
    (RUNTIME / 'requirements.lock').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    result = {'state': 'AUDITED_NOT_YET_INSTALLED', 'python': sys.version,
              'system_site_packages': False, 'owner_authority': 'Issue10 / 2026-11-25',
              'packages': rows, 'redistribution_clearance': 'NOT_GRANTED_LOCAL_EXPERIMENT_ONLY'}
    (RUNTIME / 'wheel-audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('AUDIT_READY', RUNTIME / 'wheel-audit.json')


def install():
    audit = json.loads((RUNTIME / 'wheel-audit.json').read_text(encoding='utf-8'))
    assert audit['state'] == 'AUDITED_NOT_YET_INSTALLED'
    config = (RUNTIME / 'venv/pyvenv.cfg').read_text(encoding='utf-8').lower()
    assert 'include-system-site-packages = false' in config
    for row in audit['packages']:
        data = (RUNTIME / 'wheels' / row['filename']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256']
    pip('install', '--no-index', '--find-links', str(RUNTIME / 'wheels'), '--no-deps',
        '--require-hashes', '--no-input', '-r', str(RUNTIME / 'requirements.lock'))
    pip('check')
    code = 'import importlib.metadata,json,sys; print(json.dumps({"prefix":sys.prefix,"base_prefix":sys.base_prefix,"packages":{d.metadata["Name"]:d.version for d in importlib.metadata.distributions()}}))'
    installed = json.loads(subprocess.check_output([str(python_path()), '-c', code], text=True))
    assert Path(installed['prefix']).resolve() == (RUNTIME / 'venv').resolve()
    assert installed['prefix'] != installed['base_prefix']
    audit.update(state='INSTALLED_OFFLINE_HASH_VERIFIED', installed=installed)
    (RUNTIME / 'installed.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print('ISOLATED_INSTALL_COMPLETE', python_path())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['resolve', 'install'])
    args = parser.parse_args()
    (resolve if args.operation == 'resolve' else install)()
