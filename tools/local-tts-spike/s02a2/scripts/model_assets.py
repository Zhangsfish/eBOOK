"""Explicit, hash-pinned candidate downloads into ignored storage only."""
from pathlib import Path
import argparse
import json
import shutil
import sys
import urllib.request
import uuid

SPIKE = Path(__file__).resolve().parents[2]
REPO = SPIKE.parents[1]
LOCAL = REPO / '.local-test-data/s02a2'
sys.path.insert(0, str(SPIKE / 'scripts'))
from assets import sha256, safe_relative, extract_verified


def manifest(name):
    if name not in ['matcha', 'suxin']:
        raise ValueError('Only the authorized candidate list is supported')
    return json.loads((SPIKE / 's02a2/manifests' / (name + '.json')).read_text(encoding='utf-8'))


def verify(directory, value):
    directory = Path(directory).resolve()
    for row in value['files']:
        relative = safe_relative(row['path'])
        path = (directory / relative).resolve()
        if not path.is_relative_to(directory) or not path.is_file() or path.is_symlink():
            raise ValueError('Missing/escaping candidate resource')
        if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            raise ValueError('Candidate resource mismatch: ' + row['path'])
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if actual != {row['path'] for row in value['files']}:
        raise ValueError('Unexpected candidate resource set')
    return {'status': 'PASS_RESOURCE_INTEGRITY', 'files': len(actual),
            'unpacked_bytes': sum(row['bytes'] for row in value['files'])}


def download(row, directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / safe_relative(row['filename'])
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        partial = path.with_name(path.name + '.' + uuid.uuid4().hex + '.part')
        with urllib.request.urlopen(row['url'], timeout=90) as source, partial.open('xb') as output:
            shutil.copyfileobj(source, output, 1024 * 1024)
        if partial.stat().st_size != row['bytes'] or sha256(partial) != row['sha256']:
            raise ValueError('Download mismatch; partial preserved')
        partial.rename(path)
    if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
        raise ValueError('Existing download mismatch; original preserved')
    return path


def prepare(name, destination):
    value = manifest(name)
    destination = Path(destination).resolve()
    if not destination.is_relative_to(LOCAL.resolve()):
        raise ValueError('New models must remain in ignored S02A.2 storage')
    if destination.exists():
        return verify(destination, value)
    downloads = LOCAL / 'assets/downloads'
    downloaded = [download(row, downloads) for row in value['downloads']]
    if name == 'matcha':
        subset = dict(value)
        subset['archive'] = value['downloads'][0]
        subset['files'] = [r for r in value['files'] if r['path'] != 'vocos-22khz-univ.onnx']
        subset['unpacked_bytes'] = sum(r['bytes'] for r in subset['files'])
        extract_verified(downloaded[0], destination, subset)
        shutil.copy2(downloaded[1], destination / 'vocos-22khz-univ.onnx')
    else:
        destination.mkdir(parents=True)
        for row, source in zip(value['downloads'], downloaded):
            target = destination / safe_relative(row['path'])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return verify(destination, value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['matcha', 'suxin'], required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    result = prepare(args.model, args.directory) if args.download else verify(args.directory, manifest(args.model))
    print(json.dumps(result, indent=2))
