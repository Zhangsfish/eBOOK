# S00 task memory

## Purpose and authority
Implement Issue #1 on `codex/s00-reader-foundation` only. Authority is the seven
files listed in the owner's handoff. Do not merge or begin S01.

## Workspace and provenance
- Checkout: `E:\myself\eBOOK`; the separate `lecture_asset` checkout is untouched.
- Starting commit: `ab0aa0079c74f0de17a4a7bc7facd2cbbc9532ea`.
- `Sources/ReaderCore/`: local decoding, EPUB parsing, bounded text storage,
  persistence and provider-neutral speech contracts.
- `Sources/eBOOK/`: SwiftUI app, virtualized UIKit text renderer, Apple speech.
- `Tests/`: original synthetic fixtures and core/UI tests.
- `scripts/`: deterministic fixtures, Xcode-project generation and validation.
- `.local-test-data/`: ignored generated long fixture; never commit it.
- `reports/S00_DELIVERY.md` and `reports/S00_TEST_RESULTS.md`: canonical handoff.
- `reports/S00/evidence/`: small metadata-only validation evidence; no book bodies.

## Decisions
- No runtime third-party packages or cloud speech/network implementation.
- iOS 17 minimum; a checked-in Xcode project is generated with Python stdlib.
- The owner explicitly authorized making this repository public on 2026-11-23
  to use free standard macOS Actions runners. Inspect history before changing
  visibility. No paid runner, signing, TestFlight or App Store action.
- Local host is Windows and has no Xcode. A local Python placeholder invocation
  failed; the existing `C:\conda_envs\myenv\python.exe` generated the fixture.
- Real simulator results must come from actual Xcode execution; physical-device
  audio/lock-screen claims require separate device evidence.

## Handoff
Stop at READY_FOR_AUDIT after the PR and evidence are complete. Keep unresolved
device validation and unsupported EPUB layout features explicit.

## Final implementation snapshot (2026-11-23)
- Complete-suite snapshot `5714f20c7fce3956b282d04ef10e47d11025b5ae`, successful run 45180857046; 26/26 tests, 0 skips, real Debug/Release Xcode builds.
- Exact row heights retain block 1869 across font/relaunch; window <=12 rows.
- Native Files TXT/EPUB imports use actual thumbnail selection in the UI test.
- 2d46391 later aligns chapter tops and corrects a test length; its strict long UI test passed but native Files failed at empty Recents. da6295a adds an explicit Browse wait and location-label navigation. Final HEAD has its own full CI run linked from the PR.
- Standard public macos-15-intel, Xcode 16.4, iOS 18.5 simulator.
- `evidence/PROVENANCE.json` maps logs/JSON and unmodified synthetic screenshots to their run/SHA and SHA-256.
- `evidence/source-safety.json` identifies its own separately checked source SHA.
- Final delivery has a later HEAD, identified in PR and its own CI; do not rewrite the evidence's source SHA to that later commit.
- Ignored `.local-test-data/ci/<short-sha>/` contains downloaded run caches. Scratch finalizer/selected-artifact fetch helpers are not production or canonical inputs.
- READY_FOR_AUDIT after final delivery CI succeeds; independent review pending. Physical-device audio checks and complex EPUB fidelity limits remain explicit in reports. Do not merge or start S01.
