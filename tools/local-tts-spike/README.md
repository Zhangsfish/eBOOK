# S02A isolated Kokoro spike

S02A.1 / Issue #8 updates the same branch and PR #7. The current measured native
results, exact tested revisions and remaining gates are in
`../../reports/S02A_LOCAL_TTS_FEASIBILITY.md`; `READY_FOR_AUDIT` never means GO.
Actual ARM64 and Intel iOS simulator inference and seven-case full/minimal WAV
equivalence passed at `ba17f9c6f15014e4693258ee7170dcb6c0f7e75e`.
Performance remains `PERFORMANCE_NOT_READY` (best ARM weighted RTF 1.4213),
physical-device performance is pending, and redistribution notices are incomplete.
The production reader, PR #4 and PR #5 remain untouched. This folder is the only
implementation for Issues #6/#8, plus the dedicated S02A-only workflow. The owner
has selected Kokoro; no vendor lab.

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
  `manifests/native-runtime.json`. S02A.1 downloaded and hash-verified both exact
  XCFrameworks; actual macOS `lipo` confirms device arm64 and simulator
  arm64+x86_64 for both. See `evidence/s02a1-native-audit-be36e9b.json`.
  Binary/data notices remain incomplete. No fabricated `Package.resolved`.
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
python tools/local-tts-spike/scripts/run_ios.py --model-dir MODEL_DIR --benchmark-matrix
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
The dedicated `.github/workflows/s02a-ios.yml` runs ordinary free public
`macos-15` (ARM, default after the measured matrix) or `macos-15-intel`, with public-repository and runner
allowlists. It does not edit the S00 workflow or production tests. Native build
success and actual native inference are reported separately: the initial pilot
built on Xcode 16.4 but failed before model loading because of a resource path;
the bundle lookup was corrected rather than labelling that a runtime failure.
Use the final report/CI artifacts for subsequent native results.

`--benchmark-matrix` builds once, then runs four independent native XCTest
processes for 1–4 CPU threads. Each verifies the full assets, constructs one
engine, performs an excluded warmup, and synthesizes seven original requests.
It measures constructor time, first nonempty callback, complete-waveform RTF
(arithmetic mean, nearest-rank p95, duration-weighted mean), and cumulative
process peak RSS. With seven requests, nearest-rank p95 equals the maximum.
The first request also feeds the actual WAV into AVAudioEngine and measures
request-to-first-nonzero **simulator realtime mixer** output when an audio route
exists. It is not a physical speaker/microphone audibility measurement.

No WAV, model, bundle, DerivedData or xcresult is uploaded. Only small selected
JSON and sanitized diagnostic tails go to `build/s02a-public/`; upload requires
the export guard to succeed. `artifact-manifest.json` records file hashes/sizes.
The report records the independently downloaded ZIP checks. Native metrics
must carry the actual source SHA and `IOS_SIMULATOR`; compile-only, wrong-SHA,
wrong-platform and inconsistent waveform data are rejected.

Example explicit rerun (the workflow must already be registered in GitHub):

```text
gh workflow run s02a-ios.yml --repo Zhangsfish/eBOOK --ref codex/s02a-kokoro-ios-spike -f runner=macos-15
```

`scripts/inspect_native.py` reproduces exact archive/header/lipo checks.
`scripts/audit_fst_sources.py` traces only the existing three Kokoro FSTs to a
fixed shared artifact source; it downloads no other model weights. It does not
clear the underlying grammar/data notices.

## Minimal candidate, without modifying the original pack

`scripts/make_minimal.py` verifies the full pinned pack and writes a **new**
ignored candidate plus manifest; existing destinations are refused. Ten files
retain model/voices/tokens, us-en+zh lexicons, three FSTs and LICENSE/README.
The candidate is 176,296,499 bytes; 38,930,673 bytes are omitted in the new copy.
The original archive and 377-file tree remain intact. The native matrix compares
seven actual PCM16 WAV hashes and frame counts for fresh full/candidate engines
at identical settings, warmup and request order. No output equality is inferred
from filenames, silence or source inspection. A mismatch stays NOT_PROVEN;
even a match does not establish redistribution clearance. Exact outcome is in
the report and measured evidence.
Both measured simulator runs produced bit-identical full/candidate outputs for
all seven controlled cases. The original pack remains preserved; this is a
limited tested resource equivalence, not a license or all-input guarantee.

## Bounded listening-session probe

```text
python tools/local-tts-spike/scripts/run_desktop.py --model-dir MODEL_DIR --session-seconds 600
```

This optionally generates >=600 seconds of spoken audio in bounded requests,
retaining only three session WAVs at a time. It is **not** real-time playback,
background endurance, or iOS testing. The 600/900-second probe is
NOT_RUN_PERFORMANCE_NOT_READY for S02A.1 because all measured thread
configurations remain slower than playback. Short generation results cannot
stand in for it. The original seven
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
