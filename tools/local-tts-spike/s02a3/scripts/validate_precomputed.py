"""Validate pinned author-produced diagnostic IDs; never implements a text frontend."""
from pathlib import Path
import hashlib
import json

SPIKE = Path(__file__).resolve().parents[2]


def validate_precomputed(path, pin_path=None):
    pin_path = pin_path or SPIKE / 's02a3/manifests/precomputed-ids.json'
    pins = json.loads(Path(pin_path).read_text(encoding='utf-8'))
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pins['prepared_ids_sha256']:
        raise ValueError('Author-produced ID file hash mismatch')
    value = json.loads(raw)
    source = json.loads((SPIKE / 's02a2/manifests/suxin.json').read_text(encoding='utf-8'))
    corpus_raw = (SPIKE / 'fixtures/corpus.json').read_bytes()
    corpus = json.loads(corpus_raw)['cases']
    if value.get('frontend_mode') != 'AUTHOR_PYTHON_FRONTEND_PRECOMPUTED_IDS' or value.get('end_to_end_native_text') is not False:
        raise ValueError('Precomputed IDs are not a native text frontend')
    if value.get('author_revision') != source['source_revision'] or value.get('corpus_sha256') != hashlib.sha256(corpus_raw).hexdigest():
        raise ValueError('Wrong author revision or original corpus')
    rows = value.get('records', [])
    if [r.get('fixture_id') for r in rows] != [c['id'] for c in corpus]:
        raise ValueError('Missing, reordered or substituted original case')
    for case, row in zip(corpus, rows):
        if row.get('text_sha256') != hashlib.sha256(case['text'].encode('utf-8')).hexdigest():
            raise ValueError('Different original text')
        ids = row.get('ids', [])
        if not 4 <= len(ids) <= 2048 or any(type(n) is not int or not 0 <= n < 256 for n in ids):
            raise ValueError('Invalid bounded ID tensor')
        if row.get('author_frontend_method') != 'MixedFrontend.prepare(original_unmodified_text)':
            raise ValueError('Actual author frontend provenance required')
    return {'prepared_ids_sha256': pins['prepared_ids_sha256'],
            'frontend_mode': value['frontend_mode'], 'end_to_end_native_text': False,
            'author_revision': value['author_revision'], 'validated_cases': len(rows)}
