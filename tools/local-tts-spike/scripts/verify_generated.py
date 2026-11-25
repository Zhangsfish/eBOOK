"""Validate every actual WAV header/hash and optionally fully decode via FFmpeg."""
from pathlib import Path
import argparse
import json
import subprocess
import wave
from assets import REPO, sha256


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--ffmpeg', type=Path, required=True)
    args = parser.parse_args()
    metrics = args.metrics.resolve()
    if not metrics.is_relative_to((REPO / '.local-test-data/s02a').resolve()):
        raise ValueError('Only this spike original-text outputs may be read')
    data = json.loads(metrics.read_text(encoding='utf-8'))
    if data['status'] != 'PASS_DESKTOP_ONLY':
        raise ValueError('Generation incomplete')
    rows = []
    for row in data['records']:
        path = (metrics.parent / row['wav_local_name']).resolve()
        if not path.is_relative_to(metrics.parent) or sha256(path) != row['wav_sha256']:
            raise ValueError('Waveform hash/path mismatch')
        with wave.open(str(path), 'rb') as audio:
            header = [audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getnframes()]
        if header != [1, 2, 24000, row['frames']]:
            raise ValueError('Actual PCM format/frame count mismatch')
        done = subprocess.run([str(args.ffmpeg), '-nostdin', '-v', 'error', '-i', str(path), '-f', 'null', '-'],
            capture_output=True, check=True)
        if done.stderr.strip():
            raise ValueError('Decode emitted errors')
        rows.append({'fixture_id': row['fixture_id'], 'voice': row['voice'],
                     'sha256': row['wav_sha256'], 'status': 'PASS_COMPLETE_DECODE'})
    print(json.dumps({'status': 'PASS', 'decoded_wavs': len(rows), 'records': rows}, indent=2))
