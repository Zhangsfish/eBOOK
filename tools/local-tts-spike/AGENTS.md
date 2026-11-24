# S02A isolated Kokoro feasibility

## Authority
Issue #6 and tasks/S02A_KOKORO_IOS_SPIKE.md authorize this isolated spike.
The owner has selected Kokoro; no more vendor comparisons or private book input.
The latest handoff prioritizes a reviewable PR and honest incomplete iOS results.

## Boundaries
Only tools/local-tts-spike/ and reports/S02A_LOCAL_TTS_FEASIBILITY.md may change.
Do not modify Sources/, Tests/, eBOOK.xcodeproj, STATUS.md, existing workflows,
S01 PR #4, reader PR #5, or main. Stop at READY_FOR_AUDIT; never merge/start S02B.
Do not stage any model/native binary, WAV/MP3, book, key or generated local output.

## Existing work preserved
The previous Windows listening experiment lives in the separate eBOOK worktree's
ignored .local-test-data/tts-preview/. Its private inputs/audio stay there.
Reuse only its verified public model metadata, installed isolated runtime and
model assets. Do not read or transfer private excerpt/audio into this spike.
There was no existing S02A Swift project or iOS inference result to recover.

## File map
- manifests/: exact dependency and public model pins/hashes; no model bytes.
- fixtures/: original synthetic Chinese only, never a novel.
- scripts/: integrity checks, real offline desktop benchmark, native run helper.
- Sources/ and Tests/: isolated Swift package experiment; build/run status must
  be distinguished from desktop Python results.
- evidence/: public-safe measured metadata and verification results only.
- README.md / LICENSE_REVIEW.md: reproduction and component license findings.
- ../../.local-test-data/s02a/: ignored downloads, generated speech/build outputs.

## Evidence discipline
Record tested source commit, command/environment, init, first callback latency,
audio duration/RTF and process high-water memory. Never label desktop as iOS.
Until actual iOS inference succeeds, gate remains BLOCKED_IOS_RUNTIME.
Unresolved frontend/data notices block any claim of redistribution clearance.
