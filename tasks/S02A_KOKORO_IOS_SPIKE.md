# S02A — Kokoro native iOS feasibility (READY)

GitHub Issue: https://github.com/Zhangsfish/eBOOK/issues/6
Branch: `codex/s02a-kokoro-ios-spike`

## Owner decision (2026-11-24)

**Kokoro has been selected based on public demonstrations. Google and other cloud TTS are no longer candidates.** The owner does not want another vendor/Google/Apple comparative audition. The goal is to get Kokoro working reliably, for free, on iPhone. Apple speech stays an automatic free fallback.

The earlier Issue #6 section about using a private novel excerpt for Google comparison has been superseded and removed. Do not request or access private book content for this milestone. Use only original synthetic Chinese examples.

## Why this task exists

The product must let a user listen to their own imported Chinese books for free for occasional daily sessions. Current S00 has a working Apple system-voice fallback. The remaining engineering question is whether Kokoro can provide three distinct, usable Mandarin speaker presets **fully on iPhone, without usage fees**.

This is a **native iOS proof**, not generic Python TTS research. Use one model and runtime only: Kokoro v1.1 Chinese + sherpa-onnx, preferably the ~215 MB INT8 package.

Read first: `AGENTS.md`, `docs/PRODUCT_STRATEGY_ZERO_COST_TTS.md`, `docs/PRODUCT_SPEC.md`, Issue #6, and this task. Root `STATUS.md` reflects S00 because S01 PR #4 is still awaiting merge. The current authorized scope for this branch is this S02A task; do not change STATUS, the S01 branch, or the Reader UI PR #5.

## Implementation boundaries

1. `tools/local-tts-spike/` only, plus its reports/docs. Do not modify the production iOS reader, Xcode project, core tests, `AGENTS.md`, `README.md`, existing workflows or other open PRs.
2. Use the published sherpa-onnx Swift API/Swift package with exact pinned revision, and verify the transitive binaries support the intended iOS simulator/device architecture. Avoid new build tools or package forks if upstream works.
3. Pin model source and SHA256 checksums. Separate local-only model and generated WAV output under ignored `.local-test-data/`. Never commit model weights, voice packs, downloaded binaries, generated output or commercial text. Do not upload model assets as CI artifacts or distribute them through this GitHub repo.
4. Validate actual Mandarin speech using original synthetic passages for these three Kokoro IDs: `zf_001`/sid 3, `zf_002`/sid 4, `zm_009`/sid 58. Confirm that generated WAVs are genuine speech and voices are distinguishable. This is technical verification, not a further broad voice audition. Do not use the private novel excerpt or test other providers.
5. Test Chinese text normalization, dates/numbers, punctuation, dialogue and mixed Chinese/English. Use original source-created sample text only. Produce a local sound comparison manifest with anonymous labels.
6. Verify the INT8 asset set is sufficient; quantify actual unpacked bytes, initialization seconds, audio generation wall time, audio duration/real-time factor, and peak process RSS. Separate desktop, iOS simulator, and actual iPhone device evidence.
7. Verify a Swift iOS simulator build, then **actual Chinese waveform inference on an iOS simulator** when technically supported; desktop WAV success or compile-only tests are insufficient for GO. If not executable, report `BLOCKED_IOS_RUNTIME` with exact technical evidence.
8. Exercise incremental production of multiple bounded chunks representing 10–15 minutes of occasional listening, with bounded memory/cache rather than synthesize a whole novel. This is a feasibility probe; no integration into the real App yet.
9. Produce a short model-pack download/storage/verification proposal for S02B. Include pinned URLs/hashes, cancellation/retry, user choice and Wi-Fi-first behavior. Verify individual upstream licenses and notices for voices, lexicons, tokenizer, eSpeak/data and runtime.
10. Report real commands, environment, exact tested HEAD, observed metrics and untested device claims in `reports/S02A_LOCAL_TTS_FEASIBILITY.md`. If owner iPhone unavailable, mark device latency, battery, and lock-screen behavior `NOT_RUN` instead of guessing.

## GO / NO-GO

GO requires genuine native iOS simulator Mandarin inference, reproducible original Kokoro audio, resource integrity, supported native licensing and a realistic integration plan. The owner already accepts Kokoro's demonstrated quality; sample IDs remain replaceable only if a real technical or speech defect is observed.

If unsupported or too heavy, stop and report the blocker, keep the Apple fallback functional and request further product direction. Do not pivot to paid or cloud TTS or begin a model search on your own.

## Verification and handoff

- Run all new local tests and the actual Swift native build/inference checks possible in the environment.
- Existing iOS project remains byte-for-byte unchanged in this task, so preserve the previous successful S00 CI evidence; do not claim a fresh project run unless actually performed.
- PR to main with exact tested HEAD and `READY_FOR_AUDIT`; do not self-merge, modify PR #4/#5, begin S02B, sign binaries, use paid services, register for cloud providers or publish to App Store.
