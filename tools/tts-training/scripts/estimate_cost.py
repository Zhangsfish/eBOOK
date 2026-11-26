"""Transparent AutoDL budget scenarios, never measured training results."""

import argparse
import json
import math
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config" / "cost_assumptions.json"


def preparation_cost(config: dict) -> float:
    rate = (config["no_gpu_cny_per_hour"] if config["preparation_mode_assumed"] == "no_gpu"
            else config["conservative_gpu_cny_per_hour"])
    return rate * config["no_gpu_preparation_hours"]


def estimate(audio_hours: float, config: dict) -> dict:
    examples = math.ceil(audio_hours * 3600 / config["training_example_mean_seconds"])
    effective_batch = config["per_device_batch_size"] * config["gradient_accumulation_steps"]
    steps = config["epochs"] * math.ceil(examples / effective_batch)
    teacher = [audio_hours * rtf for rtf in config["synthesis_rtf_range"]]
    preparation = [audio_hours * rtf for rtf in config["codec_preparation_rtf_range"]]
    throughput = config["optimizer_steps_per_second_range"]
    training = [steps / throughput[1] / 3600, steps / throughput[0] / 3600]
    gpu_hours = [sum(values) for values in zip(teacher, preparation, training, config["fixed_gpu_debug_export_hours_range"])]
    prep_cost = preparation_cost(config)
    total = [(hours * config["conservative_gpu_cny_per_hour"] + prep_cost + config["paid_storage_cny"])
             * (1 + config["contingency_fraction"]) for hours in gpu_hours]
    return {"status": "ESTIMATE_NOT_MEASURED", "target_audio_hours": audio_hours,
            "assumed_training_examples": examples, "optimizer_steps": steps,
            "teacher_gpu_hours": teacher, "codec_gpu_hours": preparation,
            "training_gpu_hours": training, "gpu_hours_excluding_environment_setup": gpu_hours,
            "environment_preparation_cny": prep_cost,
            "cny_with_contingency": total,
            "pcm16_stereo_48khz_gb": audio_hours * 3600 * 48000 * 2 * 2 / 1e9}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-hours", nargs="+", type=float, default=[1, 10, 20])
    parser.add_argument("--gpu-rate", type=float, help="Actual rate at instance start, CNY/hour.")
    parser.add_argument("--preparation-mode", choices=["gpu", "no_gpu"], help="Use no_gpu only when available and sufficient.")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if any(not math.isfinite(hours) or hours <= 0 for hours in args.audio_hours):
        parser.error("Audio hours must be finite and positive.")
    if args.gpu_rate is not None:
        if not math.isfinite(args.gpu_rate) or args.gpu_rate <= 0:
            parser.error("GPU rate must be finite and positive.")
        config["conservative_gpu_cny_per_hour"] = args.gpu_rate
    if args.preparation_mode:
        config["preparation_mode_assumed"] = args.preparation_mode
    pilot = [(hours * config["conservative_gpu_cny_per_hour"]
              + preparation_cost(config))
             * (1 + config["contingency_fraction"]) for hours in config["pilot_gpu_hours_range"]]
    print(json.dumps({"assumptions": config, "pilot_cny_with_contingency": pilot,
                      "scenarios": [estimate(hours, config) for hours in args.audio_hours]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
