# S02A isolated Kokoro feasibility

## Current authorization: Issue #10 / S02A.3 (2026-11-25)
The owner supersedes the historical Apple-only recommendation and authorizes
actual Suxin-Light audition with pinned free dependencies in a NEW ignored venv.
Matcha was the starting preferred candidate; after actual same-text audition the
owner replied "更喜欢 Suxin-Light". Suxin is now the preferred voice candidate,
with Matcha retained; this does not approve phone performance or redistribution.
Kokoro is paused, with no new candidates/cloud TTS. Continue PR #7 / this branch.
Read tasks/S02A3_SUXIN_MATCHA_LISTENING.md, CODEX_HANDOFF_S02A3.md and
s02a3/AGENTS.md. New report: reports/S02A3_SUXIN_MATCHA_LISTENING.md.
The existing dedicated native workflow may run a clearly labelled Suxin graph
proof with real author-produced precomputed IDs; it is not a Swift frontend.
Do not edit the production reader or start S02B. Local audition, portability and
redistribution clearance are separate gates; missing release rights do not mean
the locally generated voice failed. Stop READY_FOR_AUDIT / OWNER_LISTENING_PENDING.

## Current authorization: Issue #9 / S02A.2 (2026-11-25)
The owner explicitly supersedes the historical Kokoro-only selection below.
Continue this same branch and PR #7. Give Kokoro ONE bounded CoreML/device
attempt, then test matcha-icefall-zh-baker, screen Suxin-Light, and inspect M5-TTS
official demos/metadata only. Do not expand the shortlist or start S02B.
tasks/S02A2_MOBILE_TTS_GATE.md and tasks/CODEX_HANDOFF_S02A2.md are current.
Implementation stays here; the new report is reports/S02A2_MOBILE_TTS_EVALUATION.md.
The existing dedicated s02a-ios.yml may run these isolated proofs; do not alter
S00/S01 workflows or production code. Model/audio/build outputs remain ignored;
only small metadata and sanitized diagnostics may be public evidence.
Reuse the exact original fixtures/corpus.json for all generated candidates.
One speaker is acceptable. Native backend with precomputed IDs does not prove
a Swift text frontend. Provider symbols/listing do not prove CoreML execution.
No iPhone evidence may be inferred from simulator/desktop results. If no
candidate meets device performance and owner sound acceptance, recommend Apple
system speech and stop local-model research. See s02a2/AGENTS.md for this run.

## Authority
Issue #6 and tasks/S02A_KOKORO_IOS_SPIKE.md authorize this isolated spike.
The owner has selected Kokoro; no more vendor comparisons or private book input.
The latest handoff prioritizes a reviewable PR and honest incomplete iOS results.

## Boundaries
S02A.1 / Issue #8 (2026-11-24) explicitly extends scope to the NEW dedicated
.github/workflows/s02a-ios.yml. Existing workflow files remain untouched.
Continue this branch/PR #7 only. Native CI, thread benchmarks, public evidence,
exact binary/license inspection and controlled minimal-pack equivalence are
authorized. No production integration or new model/provider. Prior S02A metrics
are historical; preserve them and identify every new native test source SHA.

Apart from that one new S02A workflow, only tools/local-tts-spike/ and
reports/S02A_LOCAL_TTS_FEASIBILITY.md may change.
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
The historical Windows-only evidence remains distinct from new iOS results.
Unresolved frontend/data notices block any claim of redistribution clearance.

## Delivery evidence (2026-11-24)
- Actual desktop model-source commit: 691f68ed3dded6fce4e820a521253444a8a6f4e4.
  run_desktop.py and assets.py hashes in evidence/desktop-metrics.json must still
  match; no regeneration is needed merely for report-only changes.
- 7 original WAVs completed and fully decoded; all 3 selected SIDs produce
  distinct file hashes. Fresh-process initialization 9.269892 s, cumulative
  process peak working set 511217664 bytes; not controlled cold-disk startup.
- Machine speech check preserved REVIEW_ASR_DIFFERENCES: first voice was
  recognized in Traditional Chinese, others Simplified. Do not call raw sequence
  similarity pronunciation accuracy or a human quality score.
- Historical S02A: Windows native helper returned 3 / BLOCKED_IOS_RUNTIME. Swift was
  not built/run, binary architectures NOT_RUN, 10–15 min session NOT_RUN.
- LICENSE_REVIEW.md records verified root declarations and unresolved per-data
  provenance/native binary notices. This is not a redistribution clearance.
- READY_FOR_AUDIT is a delivery state, not GO for S02B. The PR must state both.

## S02A.1 measured update (2026-11-24)
- Native tested source ba17f9c6f15014e4693258ee7170dcb6c0f7e75e, Xcode 16.4.
  Intel iOS 18.6 run 45389424006 and ARM iOS 18.5 run 45392188338 passed actual
  compilation, three-voice waveform synthesis, four thread processes and seven
  full/minimal bit-identical waveform comparisons on each simulator.
- Best ARM weighted RTF 1.4212663 (2 threads); Intel 3.6103540 (3 threads).
  PERFORMANCE_NOT_READY; do not generate a wasteful 15-minute session or start
  S02B. Device latency/background/power/heat remain NOT_RUN.
- Actual simulator mixer output was observed; no physical acoustic measurement.
- Both downloaded CI ZIPs were verified against GitHub digest, CRC and per-file
  manifests: 9 UTF-8 JSON/log members each, no audio/models. Public metric JSON
  preserves tested SHA and CI URL; original ZIPs/logs remain ignored locally.
- Minimal candidate 176296499 bytes, canonical manifest SHA
  5267535f3f171cb6cb00cf17747ade8685bd63e100435e5fb9856c3965530267.
  Seven-case equivalence does not clear data/native notices or prove all-input
  compatibility. Preserve full pack and keep LICENSE_REVIEW_INCOMPLETE.
