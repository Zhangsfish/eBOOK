"""Public-safe source/evidence checks. Does not read private preview files."""
from pathlib import Path
import argparse
import json
import subprocess
from assets import REPO, SPIKE, sha256

BASE = '7d9f0e1dee06c36e5791ceac3f7064f370020ceb'
ALLOWED_REPORT = 'reports/S02A_LOCAL_TTS_FEASIBILITY.md'
ALLOWED_WORKFLOW = '.github/workflows/s02a-ios.yml'  # Explicitly authorized by Issue #8.
FORBIDDEN = {'.onnx', '.bin', '.wav', '.mp3', '.m4a', '.zip', '.bz2', '.whl', '.a', '.dylib', '.dll', '.ipa'}


def changed_files():
    raw = subprocess.check_output(['git', '-C', str(REPO), 'diff', '--name-only', '-z', BASE])
    untracked = subprocess.check_output(['git', '-C', str(REPO), 'ls-files', '--others', '--exclude-standard', '-z'])
    return sorted({p for p in (raw + untracked).decode('utf-8').split('\0') if p})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--desktop-metrics', type=Path)
    args = parser.parse_args()
    paths = changed_files()
    if not paths:
        raise RuntimeError('No delivery changes found')
    for name in paths:
        path = REPO / name
        if not (name.startswith('tools/local-tts-spike/') or name in [ALLOWED_REPORT, ALLOWED_WORKFLOW]):
            raise RuntimeError('Out-of-scope change: ' + name)
        if path.suffix.lower() in FORBIDDEN or path.stat().st_size > 262144:
            raise RuntimeError('Binary/large output must not be staged: ' + name)
    if args.desktop_metrics:
        data = json.loads(args.desktop_metrics.read_text(encoding='utf-8'))
        if data['status'] != 'PASS_DESKTOP_ONLY' or data['genuine_ios_inference']:
            raise RuntimeError('Desktop evidence status mismatch')
        if len(data['records']) != 7 or [r['voice'] for r in data['records'][:3]] != ['zf_001', 'zf_002', 'zm_009']:
            raise RuntimeError('Missing actual speaker/corpus results')
        for name, digest in data['source_file_sha256'].items():
            if sha256(SPIKE / 'scripts' / name) != digest:
                raise RuntimeError('Runtime source differs from measured source: ' + name)
        if len({r['wav_sha256'] for r in data['records'][:3]}) != 3:
            raise RuntimeError('Identical speaker waveforms')
        for row in data['records']:
            if row['completed_fraction'] < 0.999 or row['rms'] <= 0.001 or row['sample_rate'] != 24000:
                raise RuntimeError('Incomplete/silent/wrong-rate original waveform')
            if abs(row['rtf'] - row['generation_seconds'] / row['duration_seconds']) > 1e-8:
                raise RuntimeError('Inconsistent measured RTF')
    branch = subprocess.check_output(['git', '-C', str(REPO), 'branch', '--show-current'], text=True).strip()
    if branch != 'codex/s02a-kokoro-ios-spike':
        raise RuntimeError('Wrong branch')
    private_root = REPO / '.local-test-data'
    files = [p.relative_to(REPO).as_posix() for p in private_root.rglob('*') if p.is_file()]
    ignored = subprocess.run(['git', '-C', str(REPO), 'check-ignore', '--stdin', '-z'],
        input=('\0'.join(files) + '\0').encode(), capture_output=True, check=True)
    if set(ignored.stdout.decode().rstrip('\0').split('\0')) != set(files):
        raise RuntimeError('Some local output is not Git ignored')
    tracked_local = subprocess.check_output(['git', '-C', str(REPO), 'ls-files', '--', '.local-test-data'])
    if tracked_local.strip():
        raise RuntimeError('Local-only content already tracked')
    print(json.dumps({'status': 'PASS', 'scope_files_checked': len(paths), 'ignored_outputs_checked': len(files),
        'runtime_sources_match_measurement': bool(args.desktop_metrics), 'production_sources_changed': False,
        'git_head': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()}, indent=2))


if __name__ == '__main__': main()
