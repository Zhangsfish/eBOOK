"""Optional independent local ASR check using an already installed Whisper stack.

No install or model download. Only original outputs from this S02A run are read.
Machine sequence similarity is not a pronunciation accuracy or quality rating.
"""
from pathlib import Path
import argparse
import difflib
import importlib.metadata
import json
import os
import re
from assets import REPO, SPIKE, sha256


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--local-whisper-model', type=Path, required=True)
    args = parser.parse_args()
    metrics = args.metrics.resolve()
    if not metrics.is_relative_to((REPO / '.local-test-data/s02a').resolve()):
        raise ValueError('Only original S02A outputs are allowed')
    if not (args.local_whisper_model / 'model.bin').is_file():
        raise ValueError('An already downloaded local model is required')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    from faster_whisper import WhisperModel
    model = WhisperModel(str(args.local_whisper_model), device='cuda', compute_type='int8_float16', local_files_only=True)
    corpus = {r['id']: r['text'] for r in json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases']}
    measured = json.loads(metrics.read_text(encoding='utf-8'))
    def norm(text): return ''.join(re.findall('[\u4e00-\u9fffA-Za-z0-9]', text)).lower()
    rows = []
    for row in measured['records'][:3]:
        path = (metrics.parent / row['wav_local_name']).resolve()
        if not path.is_relative_to(metrics.parent) or sha256(path) != row['wav_sha256']:
            raise ValueError('Audio provenance mismatch')
        segments, info = model.transcribe(str(path), language='zh', beam_size=5,
                                          condition_on_previous_text=False, vad_filter=True)
        recognized = ''.join(segment.text for segment in segments)
        similarity = difflib.SequenceMatcher(None, norm(corpus[row['fixture_id']]), norm(recognized), autojunk=False).ratio()
        rows.append({'voice': row['voice'], 'fixture_id': row['fixture_id'], 'wav_sha256': row['wav_sha256'],
            'transcription': recognized, 'normalized_sequence_similarity': similarity,
            'status': 'LOCAL_ASR_COMPLETED_NOT_HUMAN_RATING'})
    result = {'runtime': 'faster-whisper ' + importlib.metadata.version('faster-whisper'),
        'ctranslate2': importlib.metadata.version('ctranslate2'), 'model': 'faster-whisper-large-v3',
        'device': 'cuda', 'compute_type': 'int8_float16', 'cloud_requests': 0,
        'status': 'PASS_INDEPENDENT_SPEECH_CHECK' if all(r['normalized_sequence_similarity'] >= .6 for r in rows) else 'REVIEW_ASR_DIFFERENCES',
        'records': rows}
    print(json.dumps(result, ensure_ascii=False, indent=2))
