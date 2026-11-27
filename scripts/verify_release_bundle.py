"""One strict resource validator for both unsigned device archive entry points."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_resources(app, expected_root=None):
    app = Path(app)
    expected = Path(expected_root) if expected_root else ROOT / '.local-test-data/s02b/bundle'
    manifest = json.loads((expected / 'Suxin/manifest.json').read_text())
    provenance = json.loads((expected / 'NativeNotices/runtime-provenance.json').read_text())
    names = {'model.onnx', 'config.json', 'lexicon.json', 'syllables.json', 'author-LICENSE.txt', 'pypinyin-LICENSE.txt'}
    if len(manifest['files']) != 6 or {f['path'] for f in manifest['files']} != names:
        raise ValueError('Trusted model manifest has an unexpected file set')
    if (app / 'Suxin/manifest.json').read_bytes() != (expected / 'Suxin/manifest.json').read_bytes():
        raise ValueError('Bundled model manifest differs from verified preparation')
    if {p.name for p in (app / 'Suxin').iterdir()} != names | {'manifest.json'}:
        raise ValueError('Unexpected model resource set')
    for f in manifest['files']:
        path = app / 'Suxin' / f['path']
        if path.is_symlink() or not path.is_file() or path.stat().st_size != f['bytes'] or digest(path) != f['sha256']:
            raise ValueError('Bundled model resource integrity failure')
    notices = provenance['supplemental_source_notices']
    required = {'ONNXRuntime-LICENSE.txt', 'ONNXRuntime-ThirdPartyNotices.txt'}
    if len(notices) != 2 or {f['bundle_file'] for f in notices} != required:
        raise ValueError('Both fixed-source runtime declarations are required')
    notice_names = required | {'runtime-provenance.json', 'Integration-NOTICE.md'}
    if {p.name for p in (app / 'NativeNotices').iterdir()} != notice_names:
        raise ValueError('Unexpected runtime notice resource set')
    for name in notice_names:
        path, source = app / 'NativeNotices' / name, expected / 'NativeNotices' / name
        if path.is_symlink() or not path.is_file() or digest(path) != digest(source):
            raise ValueError('Bundled runtime declaration differs from verified preparation')
    for f in notices:
        path = app / 'NativeNotices' / f['bundle_file']
        if path.stat().st_size != f['bytes'] or digest(path) != f['sha256']:
            raise ValueError('Bundled runtime declaration integrity failure')
    allowed_txt = {app / 'Suxin/author-LICENSE.txt', app / 'Suxin/pypinyin-LICENSE.txt'}
    allowed_txt.update(app / 'NativeNotices' / name for name in required)
    if set(app.rglob('*.txt')) != allowed_txt:
        raise ValueError('Unexpected text/book in App bundle')
    forbidden = {'.epub', '.wav', '.mp3', '.pcm', '.p8', '.p12', '.pem', '.key', '.dpapi'}
    if any(p.suffix.lower() in forbidden for p in app.rglob('*') if p.is_file()):
        raise ValueError('Unexpected book/audio/key in App bundle')
    return {'resource_files_verified': 6, 'runtime_source_notice_files_verified': 2,
            'model_sha256': next(f['sha256'] for f in manifest['files'] if f['path'] == 'model.onnx')}
