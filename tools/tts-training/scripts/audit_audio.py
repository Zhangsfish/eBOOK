"""Fully decode audition WAVs and verify identity; listening is a separate gate."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    import numpy as np
    import soundfile as sf

    root = args.run_directory.resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "SYNTHESIZED_UNREVIEWED"
    results = []
    for case in manifest["cases"]:
        path = root / (case["id"] + ".wav")
        assert digest(path) == case["audio_sha256"], path.name
        frames = samples = clipped = 0
        squared = peak = 0.0
        with sf.SoundFile(path) as audio:
            expected_frames = len(audio)
            for block in audio.blocks(blocksize=65536, dtype="float32", always_2d=True):
                assert np.isfinite(block).all(), path.name
                frames += block.shape[0]
                samples += block.size
                peak = max(peak, float(np.abs(block).max()))
                squared += float(np.square(block, dtype=np.float64).sum())
                clipped += int((np.abs(block) >= 0.9999).sum())
            assert frames == expected_frames and frames > 0 and peak > 1e-5, path.name
            results.append({"id": case["id"], "status": "DECODE_AND_IDENTITY_PASS",
                            "decoded_frames": frames, "sample_rate": audio.samplerate,
                            "channels": audio.channels, "audio_seconds": frames / audio.samplerate,
                            "peak": peak, "rms": (squared / samples) ** 0.5,
                            "near_full_scale_sample_fraction": clipped / samples,
                            "content_alignment": "NOT_RUN", "owner_listening": "NOT_RUN"})
    output = {"status": "DECODE_AND_IDENTITY_PASS", "cases": results,
              "asr_alignment": "NOT_RUN", "owner_approval": "NOT_RUN"}
    (root / "audio-audit.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
