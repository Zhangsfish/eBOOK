"""Create a separate cloud environment, verify resolved wheels, then install.

Use only on AutoDL. No local installation, no global environment mutation.
Torch wheel URLs must have SHA256 fragments from the official PyTorch index.
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile

from autodl_audition import cloud_only

PYTORCH_HOSTS = {"download.pytorch.org", "download-r2.pytorch.org"}


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.load(response)


def archive_sha256(download):
    archive = download["archive_info"]
    value = archive.get("hashes", {}).get("sha256")
    if value is None:
        kind, _, value = archive["hash"].partition("=")
        if kind != "sha256":
            raise ValueError("SHA256 is required.")
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("Invalid SHA256 digest.")
    return value


def verify_report(report_path, torch_urls):
    report = json.loads(report_path.read_text())
    checked = []
    for package in report["install"]:
        name = package["metadata"]["name"]
        version = package["metadata"]["version"]
        download = package["download_info"]
        digest = archive_sha256(download)
        url = download["url"]
        if name.lower() in torch_urls:
            approved = urllib.parse.urlsplit(torch_urls[name.lower()])
            assert approved.scheme == "https" and approved.hostname in PYTORCH_HOSTS
            expected = urllib.parse.parse_qs(approved.fragment)["sha256"][0]
            assert digest == expected
            if not url.startswith("file:"):
                assert urllib.parse.unquote(url.split("#")[0]) == urllib.parse.unquote(
                    torch_urls[name.lower()].split("#")[0])
            source = "official_pytorch_index"
            official_url = torch_urls[name.lower()].split("#")[0]
        else:
            official = fetch_json(f"https://pypi.org/pypi/{name}/{version}/json")
            matching = [f for f in official["urls"] if f["digests"]["sha256"] == digest]
            assert matching, name
            source = "official_pypi_release_json"
            official_url = matching[0]["url"]
        checked.append({"name": name, "version": version, "sha256": digest,
                        "verified_against": source, "official_url": official_url})
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="/root/autodl-tmp/ebook_s02a4")
    parser.add_argument("--torch-urls", required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    cloud_only(root)
    root.mkdir(parents=True, exist_ok=True)
    notes = root / "notes"
    notes.mkdir(exist_ok=True)
    environment = dict(os.environ, PIP_CACHE_DIR=str(root / "cache/pip"),
                       PIP_DISABLE_PIP_VERSION_CHECK="1", HF_HUB_DISABLE_XET="1")
    torch_urls = json.loads(Path(args.torch_urls).read_text())
    for url in torch_urls.values():
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in PYTORCH_HOSTS or "sha256=" not in parsed.fragment:
            raise ValueError("Only hash-pinned official Torch wheels are accepted.")
    python = root / ".venv/bin/python"
    if not python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(root / ".venv")], check=True)
    # Read-only reuse of complete cached wheels. Every selected wheel is still
    # independently checked against its official release before installation.
    wheelhouse = root / "cache/reused-wheels"
    wheelhouse.mkdir(parents=True, exist_ok=True)
    for candidate in sorted(Path("/tmp").glob("pip-unpack-*/*.whl")):
        link = wheelhouse / candidate.name
        if not link.exists() and zipfile.is_zipfile(candidate):
            link.symlink_to(candidate)
    torch_inputs = {}
    for name, url in torch_urls.items():
        parsed = urllib.parse.urlsplit(url)
        cached = wheelhouse / Path(urllib.parse.unquote(parsed.path)).name
        torch_inputs[name] = (cached.absolute().as_uri() + "#" + parsed.fragment) if cached.exists() else url
    requirements = [torch_inputs["torch"], torch_inputs["torchaudio"], "transformers==4.57.1",
                    "numpy==1.26.4", "sentencepiece==0.2.3", "soundfile==0.14.0",
                    "accelerate==1.15.0", "onnx==1.19.1", "onnxruntime==1.23.2",
                    "tqdm==4.67.1", "WeTextProcessing==1.3.0", "pynini==2.1.6"]
    torch_file = wheelhouse / Path(urllib.parse.unquote(urllib.parse.urlsplit(torch_urls["torch"]).path)).name
    if torch_file.exists():
        with zipfile.ZipFile(torch_file) as wheel:
            metadata_name = next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))
            metadata = wheel.read(metadata_name).decode()
        for name, version in re.findall(r"^Requires-Dist: ((?:nvidia-[\w-]+|triton))==([^;\s]+)", metadata, re.M):
            candidates = sorted(wheelhouse.glob(name.replace("-", "_") + "-" + version + "-*.whl"))
            if candidates:
                requirements.append(candidates[0].absolute().as_uri())
                print(f"REUSING {candidates[0].name}", flush=True)
    report = notes / "install-plan.json"
    common = [str(python), "-m", "pip", "install", "--index-url", "https://mirrors.aliyun.com/pypi/simple",
              "--find-links", str(wheelhouse), "--only-binary=:all:"]
    started = time.monotonic()
    subprocess.run([*common, "--dry-run", "--ignore-installed", "--report", str(report), *requirements],
                   env=environment, check=True)
    verified = verify_report(report, torch_urls)
    (notes / "package-hash-audit.json").write_text(json.dumps(verified, indent=2) + "\n")
    (notes / "requirements-official-urls.txt").write_text(
        "".join(item["official_url"] + "#sha256=" + item["sha256"] + "\n" for item in verified))
    # Install the exact, already inspected wheels from the resolution report.
    locked_urls = []
    for package in json.loads(report.read_text())["install"]:
        info = package["download_info"]
        locked_urls.append(info["url"].split("#")[0] + "#sha256=" + archive_sha256(info))
    subprocess.run([*common, "--no-deps", "--report", str(notes / "install-actual.json"), *locked_urls],
                   env=environment, check=True)
    with (notes / "requirements-lock.txt").open("w") as handle:
        subprocess.run([str(python), "-m", "pip", "freeze", "--all"], stdout=handle, check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    probe = "import json,torch,torchaudio,transformers,soundfile,importlib.metadata as m;" \
            "x=torch.ones((32,32),device='cuda');torch.cuda.synchronize();" \
            "print(json.dumps({'torch':torch.__version__,'torchaudio':torchaudio.__version__," \
            "'transformers':transformers.__version__,'cuda':torch.version.cuda,'cuda_sum':x.sum().item()," \
            "'wetext':m.version('WeTextProcessing')}))"
    output = subprocess.check_output([str(python), "-c", probe], text=True)
    result = {"status": "ENVIRONMENT_CUDA_READY", "python": str(python),
              "verified_package_count": len(verified), "seconds": time.monotonic() - started,
              "probe": json.loads(output), "training": "NOT_RUN"}
    (notes / "environment.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
