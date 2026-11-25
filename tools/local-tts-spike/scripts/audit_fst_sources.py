"""Trace ONLY the three existing Kokoro FST assets to the upstream export URL.

No other model weights are downloaded or evaluated. Matching artifact bytes is
provenance evidence, not an automatic grant/clearance for all underlying data.
"""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request
from assets import REPO, SPIKE

SOURCE = 'csukuangfj/icefall-tts-aishell3-vits-low-2024-04-06'
SOURCE_REVISION = '57345c004e13ed640e408c4c29ab56187b18f065'
FILES = {'date-zh.fst': 'data/date.fst', 'number-zh.fst': 'data/number.fst', 'phone-zh.fst': 'data/phone.fst'}


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'eBOOK-S02A1-FST-provenance'})
    with urllib.request.urlopen(req, timeout=45) as source:
        raw = source.read(4 * 1024 * 1024)
        if source.read(1):
            raise ValueError('Unexpected source size; no model weights may be downloaded')
        return raw


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=REPO / '.local-test-data/s02a1/fst-provenance.json')
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to((REPO / '.local-test-data').resolve()):
        raise ValueError('Raw audit output remains in ignored storage')
    model = json.loads(get('https://huggingface.co/api/models/' + SOURCE + '/revision/' + SOURCE_REVISION))
    revision = model['sha']
    if revision != SOURCE_REVISION:
        raise ValueError('Shared FST source revision mismatch')
    pins = {r['path']: r for r in json.loads((SPIKE / 'manifests/model.json').read_text(encoding='utf-8'))['files']}
    records = []
    for local, upstream in FILES.items():
        url = 'https://huggingface.co/' + SOURCE + '/resolve/' + revision + '/' + upstream
        raw = get(url)
        digest = hashlib.sha256(raw).hexdigest()
        records.append({'kokoro_file': local, 'upstream_file': upstream, 'source_url': url,
            'sha256': digest, 'bytes': len(raw), 'matches_pinned_kokoro_bytes':
                digest == pins[local]['sha256'] and len(raw) == pins[local]['bytes']})
    result = {'status': 'MATCHED_ARTIFACT_SOURCE' if all(r['matches_pinned_kokoro_bytes'] for r in records) else 'SOURCE_BYTES_DIFFER',
        'source_repository': 'https://huggingface.co/' + SOURCE, 'source_revision': revision,
        'declared_license': model.get('cardData', {}).get('license', 'NOT_DECLARED'),
        'original_kokoro_export_script': 'https://github.com/k2-fsa/sherpa-onnx/blob/38016c6e0622e90bf417c35e8b47e0eb805af417/.github/workflows/export-kokoro.yaml',
        'files': records, 'other_model_weights_downloaded': 0,
        'license_clearance': 'UNRESOLVED_UNDERLYING_GRAMMAR_SOURCE_AND_NOTICES'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
