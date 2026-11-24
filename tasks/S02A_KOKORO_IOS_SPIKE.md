# S02A — Kokoro native iOS feasibility (READY)

GitHub Issue: https://github.com/Zhangsfish/eBOOK/issues/6
Branch: `codex/s02a-kokoro-ios-spike`

## Why this task exists

The product must let a user listen to their own imported Chinese books for free for occasional daily sessions. Current S00 has a working Apple system-voice fallback. The next question is whether an open-source Mandarin model can provide three pleasant alternative voice presets **fully on iPhone, without usage fees**.

This is a **native iOS proof**, not generic Python TTS research. Use one model and runtime only: Kokoro v1.1 Chinese + sherpa-onnx, preferably the ~215 MB INT8 package.

Read first: `AGENTS.md`, `docs/PRODUCT_STRATEGY_ZERO_COST_TTS.md`, `docs/PRODUCT_SPEC.md`, Issue #6, and this task. Root `STATUS.md` reflects S00 because S01 PR #4 is still awaiting merge. The current authorized scope for this branch is this S02A task; do not change STATUS, the S01 branch, or the Reader UI PR #5.

## Implementation boundaries

1. `tools/local-tts-spike/` only, plus its reports/docs. Do not modify the production iOS reader, Xcode project, core tests, `AGENTS.md`, `README.md`, existing workflows or other open PRs.
2. Use the published sherpa-onnx Swift API/Swift package with exact pinned revision, and verify the transitive binaries support the intended iOS simulator/device architecture. Avoid new build tools or package forks if upstream works.
3. Pin model source and SHA256 checksums. Separate local-only model and generated WAV output under ignored `.local-test-data/`. Never commit model weights, voice packs, downloaded binaries, generated output or commercial text. Do not upload model assets as CI artifacts or distribute them through this GitHub repo.
4. Validate actual original Mandarin speech for at least three distinct trial IDs:
   - `zf_001` / speaker sid 3
   - `zf_002` / speaker sid 4
   - `zm_009` / speaker sid 58
   Also create a few alternative `zf_*`/`zm_*` trial clips if those IDs sound poor; do not claim quality before listening.
5. Test Chinese text normalization, dates/numbers, punctuation, dialogue and mixed Chinese/English. Use original source-created sample text only. Produce a local sound comparison manifest with anonymous labels.
6. Verify the INT8 asset set is sufficient; quantify actual unpacked bytes, initialization seconds, audio generation wall time, audio duration/real-time factor, and peak process RSS. Separate desktop, iOS simulator, and actual iPhone device evidence.
7. Verify a Swift iOS simulator build, then **actual Chinese waveform inference on an iOS simulator** when technically supported; desktop WAV success or compile-only tests are insufficient for GO. If not executable, report `BLOCKED_IOS_RUNTIME` with exact technical evidence.
8. Exercise incremental production of multiple bounded chunks representing 10–15 minutes of occasional listening, with bounded memory/cache rather than synthesize a whole novel. This is a feasibility probe; no integration into the real App yet.
9. Produce a short model-pack download/storage/verification proposal for S02B. Include pinned URLs/hashes, cancellation/retry, user choice and Wi-Fi-first behavior. Verify individual upstream licenses and notices for voices, lexicons, tokenizer, eSpeak/data and runtime.
10. Report real commands, environment, exact tested HEAD, observed metrics and untested device claims in `reports/S02A_LOCAL_TTS_FEASIBILITY.md`. If owner iPhone unavailable, mark device latency, battery, and lock-screen behavior `NOT_RUN` instead of guessing.

## GO / NO-GO

GO requires genuine native iOS simulator speech generation, reproducible original speech samples, verified resource integrity and a realistic integration plan. Audio quality is subjective and awaits owner hearing; the three trial speaker IDs are not product recommendations yet.

If unsupported or too heavy, stop and report evidence, suggesting another lightweight **permissively licensed offline Mandarin** candidate rather than a paid cloud service. Keep the Apple fallback functional.

## Verification and handoff

- Run all new local tests and the actual Swift native build/inference checks possible in the environment.
- Existing iOS project remains byte-for-byte unchanged in this task, so preserve the previous successful S00 CI evidence; do not claim a fresh project run unless actually performed.
- PR to main with exact tested HEAD and `READY_FOR_AUDIT`; do not self-merge, modify PR #4/#5, begin S02B, sign binaries, use paid services, register for cloud providers or publish to App Store.
