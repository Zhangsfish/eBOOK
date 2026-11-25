"""Only selected JSON metric dictionaries may leave the temporary CI runner."""
import hashlib
import json
import os
import sys
from model_assets import SPIKE, REPO, LOCAL

sys.path.insert(0, str(SPIKE / 'scripts'))
from publish_evidence import sanitize


def reject_media_payload(value):
    if isinstance(value, dict):
        if set(value) & {'samples', 'pcm', 'waveform', 'audio_base64', 'text', 'prompt', 'private_key'}:
            raise ValueError('Raw audio/text/secret payload prohibited in public metrics')
        for child in value.values(): reject_media_payload(child)
    elif isinstance(value, list):
        for child in value: reject_media_payload(child)


def main():
    output = REPO / 'build/s02a2-public'
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Preserve existing export; use a fresh CI workspace')
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, path in enumerate(sorted(LOCAL.glob('native-*/result.json'))):
        value = json.loads(path.read_text(encoding='utf-8'))
        reject_media_payload(value)
        raw = (sanitize(json.dumps(value, indent=2)) + '\n').encode('utf-8')
        if len(raw) > 256 * 1024: raise ValueError('Metrics exceed small-text limit')
        name = f'native-result-{index}.json'
        (output / name).write_bytes(raw)
        rows.append({'file': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    value = {'status': 'PASS_JSON_METRICS_ONLY', 'source_sha': os.environ.get('GITHUB_SHA'),
        'run_url': 'https://github.com/' + os.environ.get('GITHUB_REPOSITORY', 'Zhangsfish/eBOOK') + '/actions/runs/' + os.environ.get('GITHUB_RUN_ID', 'LOCAL'),
        'files': rows, 'audio_files': 0, 'model_files': 0, 'raw_profile_files': 0, 'build_artifact_files': 0}
    (output / 'artifact-manifest.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    if {p.name for p in output.iterdir()} != {r['file'] for r in rows} | {'artifact-manifest.json'}:
        raise ValueError('Unexpected export file')
    print(json.dumps(value, indent=2))


if __name__ == '__main__': main()
