"""Independent OFFLINE ASR transcript hints; not human sound-quality acceptance."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import time

REPO = Path(__file__).resolve().parents[4]
SPIKE = REPO / 'tools/local-tts-spike'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--local-whisper-model', type=Path, required=True)
    args = parser.parse_args()
    metrics_path = args.metrics.resolve()
    if not metrics_path.is_relative_to((REPO / '.local-test-data/s02a2').resolve()):
        raise ValueError('Only the original-corpus ignored experiment is permitted')
    if not (args.local_whisper_model / 'model.bin').is_file():
        raise ValueError('Use the existing local Whisper model, no download')
    metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
    if metrics['status'] != 'PASS_DESKTOP_ONLY_REAL_WAV':
        raise ValueError('Actual completed WAVs required')
    corpus = json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases']
    assert [r['fixture_id'] for r in metrics['records']] == [c['id'] for c in corpus]
    os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['TRANSFORMERS_OFFLINE'] = '1'
    from faster_whisper import WhisperModel
    model = WhisperModel(str(args.local_whisper_model), device='cuda', compute_type='int8_float16', local_files_only=True)
    result = {'status': 'LOCAL_ASR_TRANSCRIPTS_REVIEW_ONLY_NOT_OWNER_RATING',
        'faster_whisper': importlib.metadata.version('faster-whisper'),
        'ctranslate2': importlib.metadata.version('ctranslate2'),
        'model': 'local faster-whisper-large-v3', 'device': 'cuda',
        'compute_type': 'int8_float16', 'cloud_requests': 0, 'new_model_download': False,
        'source_sha': metrics['source_sha'], 'input_metrics_sha256': hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        'records': []}
    for row, case in zip(metrics['records'], corpus):
        assert row['text_sha256'] == hashlib.sha256(case['text'].encode('utf-8')).hexdigest()
        path = (metrics_path.parent / row['wav_local_name']).resolve()
        if not path.is_relative_to(metrics_path.parent) or hashlib.sha256(path.read_bytes()).hexdigest() != row['wav_sha256']:
            raise ValueError('Actual WAV provenance mismatch')
        start = time.perf_counter()
        segments, _ = model.transcribe(str(path), language='zh', beam_size=5,
            condition_on_previous_text=False, vad_filter=False)
        recognized = ''.join(segment.text for segment in segments)
        item = {'fixture_id': case['id'], 'text_sha256': row['text_sha256'],
                'wav_sha256': row['wav_sha256'], 'transcription': recognized,
                'asr_seconds': time.perf_counter() - start,
                'interpretation': 'Machine transcript only; pronunciation and sound require owner listening.'}
        result['records'].append(item)
        print(case['id'], recognized, flush=True)
    output = metrics_path.parent / 'offline-asr-review.json'
    if output.exists():
        raise FileExistsError('Preserve prior ASR output')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('LOCAL_ASR_REVIEW', output)


if __name__ == '__main__':
    main()
