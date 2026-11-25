"""Export a strict small-text allowlist. Never exports xcresult, model or WAV."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
from assets import REPO

ROOT = REPO / '.local-test-data'
OUTPUT = REPO / 'build/s02a-public'


def sanitize(text):
    text = re.sub(r'(?i)(Bearer\s+|ghp_|github_pat_)[A-Za-z0-9_\-.]+', '<REDACTED>', text)
    text = text.replace(str(REPO), '<WORKSPACE>').replace(str(Path.home()), '<HOME>')
    text = re.sub(r'\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b', '<EPHEMERAL_ID>', text)
    return '\n'.join(line for line in text.splitlines() if not any(w in line for w in ['TokenizeFromLexiconStr:', 'Lexicon matched:', 'text=']))


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    selected = [(ROOT / 's02a1/native-audit.json', 'native-audit.json')]
    for index, path in enumerate(sorted(ROOT.glob('s02a/ios-*/result.json'))):
        selected.append((path, f'ios-result-{index}.json'))
    for index, path in enumerate(sorted(ROOT.glob('s02a/ios-*/xcode-*.log'))):
        selected.append((path, f'xcode-diagnostic-{index}.log'))
    for path, name in selected:
        if not path.is_file():
            continue
        raw = path.read_text(encoding='utf-8', errors='replace')
        if name.endswith('.json'):
            raw = json.dumps(json.loads(raw), ensure_ascii=True, indent=2)
        else:
            # Keep first and last diagnostics; never publish the complete local output tree.
            raw = raw[:48000] + '\n<DIAGNOSTIC_TAIL>\n' + raw[-96000:]
        (OUTPUT / name).write_text(sanitize(raw) + '\n', encoding='utf-8')
    rows = []
    for path in OUTPUT.iterdir():
        if path.name == 'artifact-manifest.json':
            continue
        if not path.is_file() or path.suffix not in ['.json', '.log'] or path.stat().st_size > 512 * 1024:
            raise ValueError('Unexpected public evidence output')
        raw = path.read_bytes()
        raw.decode('utf-8')
        if raw.startswith((b'RIFF', b'PK\x03\x04', b'!<arch>')):
            raise ValueError('Binary output prohibited')
        rows.append({'file': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    summary = {'status': 'PASS_TEXT_ONLY_ALLOWLIST', 'source_sha': os.environ.get('GITHUB_SHA'),
        'run_url': os.environ.get('GITHUB_SERVER_URL', 'https://github.com') + '/' + os.environ.get('GITHUB_REPOSITORY', 'Zhangsfish/eBOOK') + '/actions/runs/' + os.environ.get('GITHUB_RUN_ID', 'LOCAL'),
        'audio_files': 0, 'model_files': 0, 'files': rows}
    (OUTPUT / 'artifact-manifest.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
