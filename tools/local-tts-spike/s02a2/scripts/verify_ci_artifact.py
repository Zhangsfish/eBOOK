"""Verify downloaded JSON-only CI evidence; preserve every earlier result."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile
from model_assets import LOCAL, sha256
from publish_native import reject_media_payload


def inspect(path, digest, source_sha):
    if sha256(path) != digest: raise ValueError('GitHub artifact ZIP digest mismatch')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if archive.testzip() is not None or len(set(names)) != len(names) or not 1 <= len(names) <= 20:
            raise ValueError('ZIP CRC/duplicate/count failure')
        if sum(i.file_size for i in archive.infolist()) > 2 * 1024**2:
            raise ValueError('Unexpected large metrics artifact')
        values = {}
        for info in archive.infolist():
            if not re.fullmatch(r'(artifact-manifest|native-result-[0-9]+)[.]json', info.filename) or info.file_size > 256 * 1024:
                raise ValueError('Only small selected JSON files are allowed')
            raw = archive.read(info)
            value = json.loads(raw.decode('utf-8'))
            reject_media_payload(value)
            values[info.filename] = (raw, value)
    manifest = values['artifact-manifest.json'][1]
    if manifest['source_sha'] != source_sha or any(manifest[k] != 0 for k in
            ['audio_files', 'model_files', 'raw_profile_files', 'build_artifact_files']):
        raise ValueError('Source/media/compiled output manifest failure')
    if {r['file'] for r in manifest['files']} != set(values) - {'artifact-manifest.json'}:
        raise ValueError('Artifact member set differs from manifest')
    for row in manifest['files']:
        raw = values[row['file']][0]
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Per-file digest/size mismatch')
        if values[row['file']][1]['source_sha'] != source_sha:
            raise ValueError('Actual native result source mismatch')
    return values, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--run-id', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(LOCAL.resolve()) or output.exists():
        raise ValueError('Use new ignored evidence directory; preserve previous files')
    values, manifest = inspect(args.zip, args.sha256, args.source_sha)
    output.mkdir(parents=True)
    for name, (raw, _) in values.items(): (output / name).write_bytes(raw)
    summary = {'status': 'PASS_DOWNLOADED_ZIP_CRC_DIGEST_JSON_ALLOWLIST', 'source_sha': args.source_sha,
        'run_url': 'https://github.com/Zhangsfish/eBOOK/actions/runs/' + str(args.run_id),
        'zip_sha256': args.sha256, 'zip_bytes': args.zip.stat().st_size, 'files': manifest['files'],
        'audio_files': 0, 'model_files': 0, 'raw_profile_files': 0, 'build_artifact_files': 0}
    (output / 'verified-artifact.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
