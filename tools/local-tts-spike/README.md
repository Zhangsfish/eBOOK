# S02A isolated Kokoro spike

State: `READY_FOR_AUDIT`; native iOS inference is **not yet demonstrated**.
The production reader, PR #4 and PR #5 remain untouched. This folder is the only
implementation added for Issue #6. The owner has selected Kokoro; no vendor lab.

## Reused work and new scope

The earlier local experiment had actual Windows audio and a verified official
model. It did not contain an iOS project. Its private files remain in their
original ignored folder and are not this milestone's fixtures or evidence.
This delivery reuses the same approved isolated Python runtime and read-only
verified model assets. Only the original synthetic `fixtures/corpus.json` is
read by the new benchmark. No extra package installation is required locally.

## Dependency and model pins

- Swift SPM: sherpa-onnx **2.0.3**, commit
  `38016c6e0622e90bf417c35e8b47e0eb805af417`, upstream `sherpa-onnx` static product.
- Transitive SPM ONNX Runtime **1.28.2**, package commit
  `8ebc5ebf92190903c274a7621ba4c96a732335ec`; upstream binary checksums are in
  `manifests/native-runtime.json`. They are declared pins, not downloaded-binary
  verification or architecture evidence. No fabricated `Package.resolved`.
- Windows: CPython 3.11.11, sherpa-onnx/core 2.0.3, NumPy 1.26.4. Official wheel
  URLs/bytes/hashes in `manifests/desktop-runtime.json` and hash lock file.
- INT8: `csukuangfj/kokoro-int8-multi-lang-v1_1` revision
  `1355334be009ccce397060ee639a874137a128fa`; `manifests/model.json` contains
  all 377 files, exact source URLs, bytes and SHA256. Archive 147,052,523 bytes;
  extracted pack 215,227,172 bytes. No weights/audio/native binaries in Git.

## Run without installing anything

Use the existing approved Python interpreter with the pinned dependencies.
Replace MODEL_DIR with your existing extracted official pack; verification is
read-only and refuses mismatches. Output directories are fresh UUID directories
under ignored `.local-test-data/s02a/`; existing files are not overwritten.

```text
python -m unittest discover -s tools/local-tts-spike/Tests -v
python tools/local-tts-spike/scripts/assets.py --verify MODEL_DIR
python tools/local-tts-spike/scripts/run_desktop.py --model-dir MODEL_DIR
python tools/local-tts-spike/scripts/run_ios.py --model-dir MODEL_DIR
```

The desktop run generates seven original WAVs: three same-text voice checks
(`A=zf_001/sid3`, `B=zf_002/sid4`, `C=zm_009/sid58`) plus dialogue, numbers,
polyphones and mixed Chinese/English checks using A. No original/book text is
accepted on the command line. Each request has <=240 characters and one model
is reused. Speed is 1.0 for measured results; 0.5..2.0 is an input contract,
not a claim that every rate has been tested.

Optional new model download is explicit (never part of synthesis):

```text
python tools/local-tts-spike/scripts/assets.py --download-to .local-test-data/s02a/model
```

No package is installed by these scripts. A failed or interrupted download stays
as `.part`; this spike does not implement resume. A retry must use an explicitly
new path or an inspected/verified archive. S02B's recoverable downloader is only
a proposal, not implemented in the App.

## Genuine iOS check

On macOS with Xcode and an already installed iOS simulator, `run_ios.py` stages a
fresh copy of this Swift package plus verified model resources in ignored local
storage. It runs `xcodebuild ... test`, refuses to substitute macOS execution,
and requires waveform metrics explicitly labelled `IOS_SIMULATOR` from XCTest.
Model absence is a failure, not a skipped inference test. The helper never
installs Xcode or a simulator and never uploads audio/model resources.

On Windows it exits **3 / BLOCKED_IOS_RUNTIME**, with machine-readable evidence.
The Swift code and macOS helper have **not been compiled/run on Xcode** in this
delivery. Native architecture, simulator performance and device performance are
NOT_RUN. The existing authorized public macOS workflow only runs S00; it has no
S02A entry point. Task scope restricts edits to this folder/report, so no existing
workflow, reader source or core test is altered to inject a spike run.

## Bounded listening-session probe

```text
python tools/local-tts-spike/scripts/run_desktop.py --model-dir MODEL_DIR --session-seconds 600
```

This optionally generates >=600 seconds of spoken audio in bounded requests,
retaining only three session WAVs at a time. It is **not** real-time playback,
background endurance, or iOS testing. The 600/900-second probe is NOT_RUN for this
delivery; short generation results cannot stand in for it. The original seven
validation WAVs are separate finite fixtures and are retained for local checks.

## Measurement interpretation

Initialization is a fresh-process model constructor after asset hash verification;
OS disk cache is not cold-controlled. First callback latency is measured from
the real generation call to the first nonempty native callback. RTF is generation
wall time / actual PCM duration, not playback speed. RSS is cumulative process
high-water memory, not per-voice memory or an iPhone projection. A distinct PCM
hash proves outputs differ, not a subjective voice ranking or pronunciation score.

Optional independent speech-content checks use existing external tools only:

```text
python tools/local-tts-spike/scripts/verify_generated.py --metrics LOCAL_METRICS --ffmpeg EXISTING_FFMPEG
python tools/local-tts-spike/scripts/check_speech.py --metrics LOCAL_METRICS --local-whisper-model EXISTING_LOCAL_LARGE_V3
```

The ASR helper reads only this spike's original outputs, uses a pre-existing
faster-whisper/CUDA environment and cached model, and never downloads/installs.
Set `PYTHONIOENCODING=utf-8` for redirected Unicode output on Windows, or decode
the captured file using that interpreter's actual stdout encoding. Its exact
versions and machine sequence differences are in `evidence/original-asr.json`.
This is not a human listening grade or validation of all number/polyphone readings.

See `LICENSE_REVIEW.md` before any model/runtime redistribution, and
`../../reports/S02A_LOCAL_TTS_FEASIBILITY.md` for the exact tested source commit,
real metrics, remaining gates and audit handoff.
