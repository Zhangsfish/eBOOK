"""Plan locally; fetch and synthesize only inside an AutoDL Linux workspace.

No package installation and no training. Run the pinned official inference CLI
serially, retaining per-case logs and a manifest even after failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import time
import urllib.request

LAB = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checked_file(path: Path, item: dict) -> None:
    if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
        raise ValueError(f"Identity mismatch: {path}")


def cloud_only(workspace: Path) -> None:
    cloud_root = Path("/root/autodl-tmp")
    if platform.system() != "Linux" or not cloud_root.is_dir():
        raise RuntimeError("fetch/run require AutoDL Linux; use plan on the local computer.")
    if not workspace.is_relative_to(cloud_root.resolve()) or workspace == cloud_root.resolve():
        raise ValueError("Use a dedicated directory under /root/autodl-tmp.")


def run_command(command: list[str], **kwargs) -> str:
    return subprocess.check_output(command, text=True, **kwargs).strip()


def verify_source(source: Path, lock: dict) -> None:
    if run_command(["git", "-C", str(source), "rev-parse", "HEAD"]) != lock["code"]["revision"]:
        raise ValueError("Upstream source revision mismatch.")
    if run_command(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"]):
        raise ValueError("Upstream tracked source has local modifications.")
    checked_file(source / lock["reference"]["path"], lock["reference"])


def fetch_assets(workspace: Path, lock: dict) -> None:
    cloud_only(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    source = workspace / "upstream"
    if not source.exists():
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout",
                        lock["code"]["url"], str(source)], check=True, timeout=180)
        subprocess.run(["git", "-C", str(source), "checkout", "--detach",
                        lock["code"]["revision"]], check=True, timeout=180)
    verify_source(source, lock)
    for model in lock["models"]:
        for item in model["files"]:
            relative = PurePosixPath(item["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe model file path.")
            dest = workspace / "models" / model["local_name"] / relative
            if dest.exists():
                checked_file(dest, item)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://huggingface.co/{model['repo']}/resolve/{model['revision']}/{item['path']}"
            partial = dest.with_name(dest.name + ".part")
            request = urllib.request.Request(url, headers={"User-Agent": "eBOOK-S02A4"})
            with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    out.write(chunk)
            checked_file(partial, item)
            partial.replace(dest)
            print(f"VERIFIED {model['local_name']}/{item['path']}", flush=True)


def load_cases() -> list[dict]:
    cases = []
    for name in ("teacher_audition.json", "continuous_audition_20261125.json"):
        data = json.loads((LAB / "fixtures" / name).read_text(encoding="utf-8"))
        if data["split"] != "teacher_selection" or data["student_training_allowed"] is not False:
            raise ValueError("These fixtures must remain teacher-selection-only.")
        cases.extend(data["cases"])
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Duplicate audition case IDs.")
    for case in cases:
        if not case["id"].replace("_", "").isalnum() or not case["text"].strip():
            raise ValueError("Invalid audition case.")
    return cases


def inference_command(workspace, run_dir, case: dict, python: str | None = None) -> list[str]:
    return [python or sys.executable, str(workspace / "upstream" / "infer.py"),
            "--checkpoint", str(workspace / "models" / "MOSS-TTS-Nano"),
            "--audio-tokenizer-pretrained-name-or-path", str(workspace / "models" / "MOSS-Audio-Tokenizer-Nano"),
            "--prompt-audio-path", str(workspace / "upstream" / "assets" / "audio" / "zh_6.wav"),
            "--mode", "voice_clone", "--device", "cuda", "--dtype", "bfloat16",
            "--text-file", str(run_dir / (case["id"] + ".txt")),
            "--output-audio-path", str(run_dir / (case["id"] + ".wav")),
            "--seed", "42", "--max-new-frames", "375", "--voice-clone-max-text-tokens", "75",
            "--text-temperature", "1.0", "--text-top-p", "1.0", "--text-top-k", "50",
            "--audio-temperature", "0.8", "--audio-top-p", "0.95", "--audio-top-k", "25",
            "--audio-repetition-penalty", "1.2", "--print-voice-clone-text-chunks"]


def synthesize(workspace: Path, run_dir: Path, lock: dict, cases: list[dict], max_seconds: int) -> None:
    cloud_only(workspace)
    import soundfile  # Official inference dependency; imported only after the cloud guard.

    verify_source(workspace / "upstream", lock)
    for model in lock["models"]:
        for item in model["files"]:
            checked_file(workspace / "models" / model["local_name"] / item["path"], item)
    hardware = run_command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    # A new folder avoids confusing partial or older audio with this attempt.
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "status": "RUNNING", "hardware": hardware,
                "sources_lock_sha256": sha256(LAB / "config" / "sources.lock.json"),
                "sampling_identity": "pinned_infer_resolve_sampling_kwargs_defaults_explicit",
                "official_demo_exact_sampling_known": False,
                "training": "NOT_RUN", "owner_new_audio_approval": "NOT_RUN",
                "alignment_review": "NOT_RUN", "device_verification": "NOT_RUN", "cases": []}
    manifest_path = run_dir / "manifest.json"

    def save() -> None:
        temporary = manifest_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(manifest_path)

    started = time.monotonic()
    environment = dict(os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONUNBUFFERED="1")
    try:
        save()
        for case in cases:
            remaining = max_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError("Audition process time budget exhausted; instance billing continues until shutdown.")
            text_path = run_dir / (case["id"] + ".txt")
            text_path.write_text(case["text"], encoding="utf-8")
            command = inference_command(workspace, run_dir, case)
            record = {"id": case["id"], "split": "teacher_selection", "status": "RUNNING",
                      "text_sha256": sha256(text_path), "command": command}
            manifest["cases"].append(record)
            save()
            case_started = time.monotonic()
            with (run_dir / (case["id"] + ".log")).open("w", encoding="utf-8") as log:
                subprocess.run(command, cwd=workspace / "upstream", env=environment, stdout=log,
                               stderr=subprocess.STDOUT, timeout=remaining, check=True)
            audio_path = run_dir / (case["id"] + ".wav")
            audio = soundfile.info(str(audio_path))
            duration = audio.frames / audio.samplerate
            if duration <= 0:
                raise ValueError("Empty generated WAV.")
            record.update(sample_rate=audio.samplerate, channels=audio.channels,
                          subtype=audio.subtype, audio_seconds=duration)
            record.update(status="SYNTHESIZED_UNREVIEWED", wall_seconds=time.monotonic() - case_started,
                          audio_bytes=audio_path.stat().st_size, audio_sha256=sha256(audio_path))
            record["wall_rtf_including_model_load"] = record["wall_seconds"] / duration
            save()
        manifest["status"] = "SYNTHESIZED_UNREVIEWED"
    except BaseException as exc:
        manifest["status"] = "FAILED"
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        if manifest["cases"] and manifest["cases"][-1]["status"] == "RUNNING":
            manifest["cases"][-1]["status"] = "FAILED"
        raise
    finally:
        manifest["wall_seconds"] = time.monotonic() - started
        save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "fetch", "run"])
    parser.add_argument("--workspace", default="/root/autodl-tmp/ebook_s02a4")
    parser.add_argument("--run-id", default="audition-001")
    parser.add_argument("--max-seconds", type=int, default=7200)
    args = parser.parse_args()
    if not args.run_id.replace("-", "").replace("_", "").isalnum() or args.max_seconds <= 0:
        parser.error("Use a safe run ID and a positive max-seconds value.")
    lock = json.loads((LAB / "config" / "sources.lock.json").read_text(encoding="utf-8"))
    cases = load_cases()
    if args.action == "plan":
        workspace = PurePosixPath(args.workspace)
        if not workspace.is_absolute():
            parser.error("Plan workspace must be an absolute AutoDL Linux path.")
        run_dir = workspace / "runs" / args.run_id
        print(json.dumps({"status": "PLAN_ONLY_NOT_RUN", "cloud_execution_required": True,
                          "model_download_bytes": sum(f["bytes"] for m in lock["models"] for f in m["files"]),
                          "commands": [inference_command(workspace, run_dir, case, "python") for case in cases],
                          "process_timeout_seconds": args.max_seconds,
                          "timeout_stops_instance_billing": False}, ensure_ascii=False, indent=2))
    else:
        workspace = Path(args.workspace).expanduser().resolve()
        run_dir = workspace / "runs" / args.run_id
        if args.action == "fetch":
            fetch_assets(workspace, lock)
        else:
            synthesize(workspace, run_dir, lock, cases, args.max_seconds)


if __name__ == "__main__":
    main()
