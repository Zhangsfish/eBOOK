"""CPU-only checks for cloud isolation, asset identity and budget units."""

import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

LAB = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, LAB / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    for path in (LAB / "scripts").glob("*.py"):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    audition = load("autodl_audition")
    cost = load("estimate_cost")
    result = subprocess.run([sys.executable, str(LAB / "scripts/autodl_audition.py"), "plan"],
                            capture_output=True, text=True, encoding="utf-8", check=True)
    plan = json.loads(result.stdout)
    assert plan["status"] == "PLAN_ONLY_NOT_RUN"
    assert len(plan["commands"]) == 7
    assert all(c[0] == "python" and c[1] == "/root/autodl-tmp/ebook_s02a4/upstream/infer.py"
               for c in plan["commands"])
    local_refusal = "NOT_RUN_ON_AUTODL"
    if platform.system() != "Linux" or not Path("/root/autodl-tmp").is_dir():
        for action in ("fetch", "run"):
            result = subprocess.run([sys.executable, str(LAB / "scripts/autodl_audition.py"), action],
                                    capture_output=True, text=True, encoding="utf-8")
            assert result.returncode != 0 and "require AutoDL Linux" in result.stderr
        local_refusal = "PASS"
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "asset.bin"
        path.write_bytes(b"original")
        identity = {"bytes": 8, "sha256": audition.sha256(path)}
        audition.checked_file(path, identity)
        for corrupt in (b"changed!", b"short"):
            path.write_bytes(corrupt)
            try:
                audition.checked_file(path, identity)
            except ValueError:
                pass
            else:
                raise AssertionError("Asset corruption was accepted.")
    config = json.loads(cost.CONFIG.read_text(encoding="utf-8"))
    budget = cost.estimate(10, config)
    assert budget["optimizer_steps"] == 1125
    assert abs(budget["cny_with_contingency"][0] - 32.7760875) < 1e-8
    assert abs(budget["cny_with_contingency"][1] - 97.153875) < 1e-8
    assert abs(budget["pcm16_stereo_48khz_gb"] - 6.912) < 1e-8
    assert "torch" not in sys.modules and "soundfile" not in sys.modules
    print(json.dumps({"status": "PASS", "cloud_plan_cases": 7, "local_fetch_run_refusal": local_refusal,
                      "corrupt_asset_refusal": "PASS", "budget_units": "PASS",
                      "model_imports": "NONE", "synthesis_training_export": "NOT_RUN"}, indent=2))


if __name__ == "__main__":
    main()
