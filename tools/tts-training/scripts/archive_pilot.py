"""Archive this pilot's sources, fixed models and evidence without environment caches."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

from autodl_audition import checked_file, cloud_only


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="/root/autodl-tmp/ebook_s02a4")
    parser.add_argument("--name", default="s02a4_pilot_20261126")
    args = parser.parse_args()
    if not args.name.replace("_", "").replace("-", "").isalnum():
        parser.error("Use a safe archive name.")
    root = Path(args.workspace).resolve()
    cloud_only(root)
    lock_path = root / "harness/tools/tts-training/config/sources.lock.json"
    lock = json.loads(lock_path.read_text())
    selected = set()
    for directory in ("harness", "models", "runs", "notes", "logs"):
        for path in (root / directory).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and not path.name.endswith(".part"):
                if path.name not in {"archive-members.json", "archive-identity.json"}:
                    selected.add(path)
    for model in lock["models"]:
        for item in model["files"]:
            checked_file(root / "models" / model["local_name"] / item["path"], item)
    source = root / "upstream"
    paths = subprocess.check_output(["git", "-C", str(source), "ls-files", "-z"]).decode().split("\0")
    for name in paths:
        if not name or name.startswith("finetuning/datasets/"):
            continue
        if name.startswith("assets/") and name != lock["reference"]["path"]:
            continue
        path = source / name
        if path.is_file():
            selected.add(path)
    selected.add(root / "torch_wheels.json")
    members = []
    for path in sorted(selected):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Unexpected path in archive: {path}")
        members.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                        "sha256": sha256(path)})
    member_path = root / "notes/archive-members.json"
    member_path.write_text(json.dumps({"files": members}, indent=2) + "\n")
    outputs = root / "outputs"
    outputs.mkdir(exist_ok=True)
    archive = outputs / (args.name + ".tar.gz")
    if archive.exists():
        raise FileExistsError("Keep the earlier archive; choose a new name.")
    temporary = archive.with_suffix(".gz.part")
    with tarfile.open(temporary, "w:gz", compresslevel=3) as tar:
        for item in members:
            tar.add(root / item["path"], arcname=item["path"], recursive=False)
        tar.add(member_path, arcname="notes/archive-members.json", recursive=False)
    temporary.replace(archive)
    result = {"archive": archive.name, "bytes": archive.stat().st_size, "sha256": sha256(archive),
              "hashed_members": len(members), "tar_members": len(members) + 1}
    (root / "notes/archive-identity.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
