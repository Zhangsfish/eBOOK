"""Prepare a separate Matcha package for an already-authorized signed Mac test.

No signing, device selection, provisioning, installation or inference occurs here.
Kokoro's final attempt is closed; this helper must not restart that experiment.
"""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import uuid
from model_assets import SPIKE, REPO, LOCAL, manifest, verify, sha256
from run_native import PINS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=Path, required=True)
    args = parser.parse_args()
    verify(args.model_dir, manifest('matcha'))
    destination = LOCAL / ('device-matcha-' + uuid.uuid4().hex)
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copy2(SPIKE / 'Package.swift', destination)
    for name in ['Sources', 'Tests']:
        shutil.copytree(SPIKE / name, destination / name, ignore=shutil.ignore_patterns('__pycache__'))
    resources = destination / 'Tests/LocalTTSSpikeTests/Resources'
    shutil.copytree(args.model_dir, resources / 'matcha')
    shutil.copy2(SPIKE / 's02a2/manifests/matcha.json', resources / 'matcha-model.json')
    shutil.copy2(SPIKE / 'fixtures/corpus.json', resources / 'corpus.json')
    context = {
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'execution_worktree_dirty': bool(subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain'])),
        'staging_script_sha256': sha256(Path(__file__)), 'phase': 'matcha-device-plan',
        'runtime_revision': PINS['sherpa-onnx'], 'corpus_sha256': sha256(resources / 'corpus.json'),
        'device_test_status': 'NOT_RUN_STAGING_ONLY',
    }
    (resources / 's02a2-context.json').write_text(json.dumps(context, indent=2) + '\n', encoding='utf-8')
    print('STAGED_ONLY_NO_SIGNING_OR_TEST', destination)


if __name__ == '__main__': main()
