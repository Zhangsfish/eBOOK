"""Pinned public assets only. Verification never installs or downloads implicitly."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import shutil
import tarfile
import urllib.request

SPIKE = Path(__file__).resolve().parents[1]
REPO = SPIKE.parents[1]
MANIFEST = SPIKE / 'manifests/model.json'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(name):
    part = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or part.is_absolute() or '..' in part.parts:
        raise ValueError('Unsafe asset member')
    return part


def verify(model_dir, manifest=None):
    model_dir = Path(model_dir).resolve()
    manifest = manifest or json.loads(MANIFEST.read_text(encoding='utf-8'))
    expected = manifest['files']
    for row in expected:
        relative = safe_relative(row['path'])
        path = (model_dir / relative).resolve()
        if not path.is_relative_to(model_dir) or not path.is_file():
            raise ValueError('Missing/escaping asset: ' + row['path'])
        if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            raise ValueError('Asset integrity mismatch: ' + row['path'])
    actual = {p.relative_to(model_dir).as_posix() for p in model_dir.rglob('*') if p.is_file()}
    if actual != {r['path'] for r in expected}:
        raise ValueError('Unexpected asset set')
    return {'status': 'PASS', 'files': len(expected), 'unpacked_bytes': sum(r['bytes'] for r in expected),
            'model_manifest_sha256': sha256(MANIFEST)}


def extract_verified(archive, destination, manifest=None):
    """Extract into a NEW directory only; reject links, traversal and oversized data."""
    manifest = manifest or json.loads(MANIFEST.read_text(encoding='utf-8'))
    if sha256(archive) != manifest['archive']['sha256'] or Path(archive).stat().st_size != manifest['archive']['bytes']:
        raise ValueError('Archive integrity mismatch')
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('Preserve existing assets; choose a new destination')
    with tarfile.open(archive, 'r:bz2') as source:
        members = source.getmembers()
        if len(members) > 2000 or sum(m.size for m in members if m.isfile()) != manifest['unpacked_bytes']:
            raise ValueError('Unexpected archive size')
        files = set()
        for member in members:
            rel = safe_relative(member.name)
            if rel.parts[0] != manifest['directory'] or not (member.isdir() or member.isfile()):
                raise ValueError('Unexpected member/link')
            if member.isfile():
                inner = PurePosixPath(*rel.parts[1:]).as_posix()
                if inner in files:
                    raise ValueError('Duplicate member')
                files.add(inner)
        if files != {r['path'] for r in manifest['files']}:
            raise ValueError('Archive member set mismatch')
        destination.mkdir(parents=True)
        for member in members:
            rel = safe_relative(member.name)
            target = destination.joinpath(*rel.parts[1:])
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as incoming, target.open('xb') as output:
                    shutil.copyfileobj(incoming, output)
    return verify(destination, manifest)


def prepare(destination):
    """Explicit model-only download. No book input, inference service or account."""
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    local = (REPO / '.local-test-data/s02a').resolve()
    destination = Path(destination).resolve()
    if not destination.is_relative_to(local):
        raise ValueError('Downloaded assets must stay in ignored .local-test-data/s02a')
    archive = local / 'downloads' / 'kokoro-int8-multi-lang-v1_1.tar.bz2'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        partial = archive.with_suffix(archive.suffix + '.part')
        # Never replace an earlier interrupted partial: it remains available for inspection.
        with urllib.request.urlopen(manifest['archive']['url'], timeout=90) as incoming, partial.open('xb') as target:
            shutil.copyfileobj(incoming, target, 1024 * 1024)
        if sha256(partial) != manifest['archive']['sha256']:
            raise ValueError('Download checksum mismatch; partial preserved')
        partial.rename(archive)
    return extract_verified(archive, destination, manifest)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--download-to', type=Path)
    args = parser.parse_args()
    if bool(args.verify) == bool(args.download_to):
        parser.error('Choose exactly one operation')
    print(json.dumps(verify(args.verify) if args.verify else prepare(args.download_to), indent=2))
