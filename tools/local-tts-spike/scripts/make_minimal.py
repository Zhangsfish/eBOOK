"""Copy a NEW minimal candidate; preserve the full pack. No equivalence claim here."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from assets import REPO, SPIKE, verify

REQUIRED = {'model.int8.onnx', 'voices.bin', 'tokens.txt', 'lexicon-us-en.txt', 'lexicon-zh.txt',
            'date-zh.fst', 'number-zh.fst', 'phone-zh.fst', 'LICENSE', 'README.md'}


def create_candidate(full_dir, destination, manifest_output):
    manifest = json.loads((SPIKE / 'manifests/model.json').read_text(encoding='utf-8'))
    verify(full_dir, manifest)
    destination = Path(destination).resolve()
    manifest_output = Path(manifest_output).resolve()
    local = (REPO / '.local-test-data').resolve()
    if not destination.is_relative_to(local) or not manifest_output.is_relative_to(local):
        raise ValueError('Candidate models/manifests must remain local ignored storage')
    if destination.exists() or manifest_output.exists():
        raise FileExistsError('Preserve previous candidate; use new destination/output')
    rows = [r for r in manifest['files'] if r['path'] in REQUIRED]
    if {r['path'] for r in rows} != REQUIRED:
        raise ValueError('Missing required pinned minimal member')
    destination.mkdir(parents=True)
    for row in rows:
        shutil.copy2(Path(full_dir) / row['path'], destination / row['path'])
    result = {'status': 'CANDIDATE_UNTIL_CONTROLLED_AUDIO_EQUIVALENCE',
        'model': manifest['model'], 'precision': manifest['precision'], 'revision': manifest['revision'],
        'files': rows, 'unpacked_bytes': sum(r['bytes'] for r in rows), 'full_pack_bytes': manifest['unpacked_bytes'],
        'removed_bytes': manifest['unpacked_bytes'] - sum(r['bytes'] for r in rows),
        'removed_paths': [r['path'] for r in manifest['files'] if r['path'] not in REQUIRED],
        'equivalence': 'NOT_RUN', 'distribution_clearance': 'UNRESOLVED_DATA_NOTICES'}
    canonical = json.dumps({'revision': result['revision'], 'files': rows}, sort_keys=True, separators=(',', ':')).encode()
    result['canonical_manifest_sha256'] = hashlib.sha256(canonical).hexdigest()
    verify(destination, result)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--full-dir', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--manifest-output', type=Path, required=True)
    args = parser.parse_args()
    data = create_candidate(args.full_dir, args.destination, args.manifest_output)
    print(json.dumps({k: v for k, v in data.items() if k not in ['files', 'removed_paths']}, indent=2))
