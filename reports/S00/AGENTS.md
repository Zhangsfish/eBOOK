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
