"""Load the real Suxin graph using an existing ORT; never invent speech IDs.

This deliberately stops before inference when the author frontend is unavailable.
No packages are installed and no network request is made by this script.
"""
from pathlib import Path
import argparse
import json
import platform
import subprocess
import time
import uuid
from model_assets import SPIKE, REPO, LOCAL, manifest, verify, sha256
from benchmark_desktop import peak_rss


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--load-only', action='store_true', required=True)
    args = parser.parse_args()
    integrity = verify(args.model_dir, manifest('suxin'))
    import onnxruntime as ort
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    start = time.perf_counter()
    session = ort.InferenceSession(str(args.model_dir / 'zh_en-suxin-light.int8-excldec.onnx'),
                                   options, providers=['CPUExecutionProvider'])
    elapsed = time.perf_counter() - start
    result = {
        'status': 'MODEL_LOAD_ONLY_NO_SPEECH_INFERENCE',
        'environment': 'WINDOWS_DESKTOP_CPU' if platform.system() == 'Windows' else 'DESKTOP_CPU',
        'source_sha': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'execution_worktree_dirty': bool(subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain'])),
        'source_file_sha256': sha256(Path(__file__)),
        'model_integrity': integrity, 'onnxruntime': ort.__version__, 'threads': 4,
        'genuine_audio_generation': False, 'genuine_ios_inference': False,
        'frontend': 'NOT_RUN_DEPENDENCY_APPROVAL_PENDING',
        'model_initialization_seconds': elapsed, 'peak_process_rss_bytes': peak_rss(),
        'inputs': [dict(name=i.name, shape=i.shape, type=i.type) for i in session.get_inputs()],
        'outputs': [dict(name=i.name, shape=i.shape, type=i.type) for i in session.get_outputs()],
        'actual_providers': session.get_providers(), 'custom_op_libraries_registered': 0,
        'rtf': 'NOT_RUN_NO_SPEECH', 'first_audible_output': 'NOT_RUN_NO_SPEECH',
        'cloud_api_calls': 0,
    }
    destination = LOCAL / 'outputs' / ('suxin-load-only-' + uuid.uuid4().hex)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    print('SUXIN_LOAD_ONLY_RESULT', destination / 'metrics.json')


if __name__ == '__main__': main()
