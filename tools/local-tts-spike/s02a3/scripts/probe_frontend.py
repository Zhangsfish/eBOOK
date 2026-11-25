"""Bounded diagnostic of first-use English frontend vs warmed real speech."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
from benchmark_suxin import REPO, SPIKE, manifest, verify, sha256, peak_rss, write_wave


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=Path, required=True)
    args = parser.parse_args()
    verify(args.model_dir, manifest('suxin'))
    sys.path.insert(0, str(args.model_dir.resolve()))
    import numpy as np
    from suxin_tts import SuxinTTS
    case = next(c for c in json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases'] if c['id'] == 'mixed')
    output = REPO / '.local-test-data/s02a2/s02a3/outputs' / ('frontend-probe-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    result = {'environment': 'WINDOWS_DESKTOP_CPU', 'status': 'RUNNING',
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_file_sha256': sha256(Path(__file__)),
        'text_sha256': hashlib.sha256(case['text'].encode('utf-8')).hexdigest(),
        'fixture_id': 'mixed', 'threads': 4, 'genuine_ios_inference': False,
        'human_quality': 'OWNER_PREFERS_SUXIN_SHORT_AUDITION', 'cloud_requests': 0,
        'frontend_prepare_seconds': [], 'warmed_speech': [], 'physical_first_audible': 'NOT_RUN'}
    start = time.perf_counter(); tts = SuxinTTS.from_pretrained(args.model_dir, intra_op_num_threads=4)
    result['model_initialization_seconds'] = time.perf_counter() - start
    try:
        for _ in range(2):
            start = time.perf_counter(); ids, phonemes = tts.frontend.prepare(case['text'])
            result['frontend_prepare_seconds'].append(time.perf_counter() - start)
        for index in range(2):
            start = time.perf_counter(); audio = tts.synthesize_long(case['text'])
            elapsed = time.perf_counter() - start
            row = write_wave(output / ('mixed-warm-' + str(index) + '.wav'), audio, np)
            result['warmed_speech'].append(dict(row, generation_seconds=elapsed, rtf=elapsed / row['duration_seconds']))
        result.update(status='PASS_ACTUAL_AUTHOR_FRONTEND_AND_WARM_SPEECH',
            missing_phonemes=tts.frontend.missing_phonemes, peak_process_rss_bytes=peak_rss())
    finally:
        tts.close()
        (output / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print('FRONTEND_PROBE', output / 'metrics.json', result['status'])


if __name__ == '__main__':
    main()
