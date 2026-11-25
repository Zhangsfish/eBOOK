# S02A.3 — Matcha + real Suxin-Light audition (READY)

Issue: https://github.com/Zhangsfish/eBOOK/issues/10
Existing PR: https://github.com/Zhangsfish/eBOOK/pull/7
Existing branch: `codex/s02a-kokoro-ios-spike`

## Explicit owner decision — supersedes the former blanket NO-GO recommendation

The owner is the product decision-maker. **Matcha is the leading local AI option**, based on existing iOS simulator speed tests. **Suxin-Light is authorized for actual end-to-end voice testing**; its past load-only state did not evaluate speech speed or listenability. Do not silently reject it because installing missing frontend packages was deferred. Owner approval of a particular model's sound remains pending direct listening.

The former S02A.2 recommendation to abandon all local AI voices is not binding. Keep Apple system speech as a fallback; no cloud TTS, Google or spending.

## Important established facts

- Matcha zh-baker: iOS simulator 4T weighted RTF 0.5759 and p95 1.0837 across five short original cases. The measured 9.815-second first full-block mixer output does **not** pass a user-facing <=5-second target. True physical iPhone performance and continuous playback remain untested.
- Suxin-Light: pinned ONNX graph loaded in Windows ORT 1.20.1 in 6.590s with ~170.72 MiB peak process RSS. **No text-to-audio synthesis, RTF, WAV, or sound evaluation occurred.** A technical dependency approval blocker was reported, not a failed model.
- Public Suxin model card: MIT for weights/inference code; front end uses pypinyin (Chinese) and Piper/eSpeak (English). Native iOS and GPL/third-party redistribution obligations are still unresolved.

## Mandatory sequence

1. Inspect current branch/worktree, preserve old outputs and tested evidence. Reuse pinned models, the existing five-case synthetic corpus and local-only audio.
2. Create a **new project-isolated virtualenv** below ignored `.local-test-data/s02a2/`. The owner now authorizes running Suxin tests; within that narrow scope, install necessary **free** frontend dependencies with recorded versions/hashes, using only safe package sources, without touching system/global Python, pre-existing environments or other projects. Prefer the versions already in `tools/local-tts-spike/s02a2/manifests/suxin-frontend-proposal.json`; verify actual dependency and licenses.
3. Use the author's original Suxin frontend and synthesizer on the same original Chinese passages used by Matcha. Generate and verify real WAVs, record model+asset revision, text SHA, package versions, RTF, startup, peak memory, English OOV, pronunciation and model failure cases. Do not fabricate phoneme tokens or replace failed samples with another model.
4. Update the local A/B listening package: **Matcha versus Suxin first**; Kokoro optional baseline. Original text only, no book excerpts. Clearly label which clips are real native/desktop. Give owner a simple HTML player and ZIP under ignored local storage. This is the **owner listening gate**. Do not infer subjective quality from model specs or ASR.
5. If actual desktop Suxin speech is viable, test the existing iOS bridge with author-frontended phoneme IDs as a clearly labelled backend-only proof. Only claim **full iOS text-to-audio** when equivalent native Chinese frontend is genuinely implemented and run. Time-box complex porting; do not require a full iPhone implementation before the owner has listened to Suxin.
6. Keep Matcha as preferred existing option; after owner listening, prepare (do not yet implement in production) a bounded audio prebuffer / early-audio approach, real-device test and licensing plan.
7. Keep packaging/redistribution legal review separate from audition: no claim of App Store rights without explicit evidence for exact model weights, vocoder, lexicon/FST, ONNX runtime and Piper/eSpeak dependencies. Unresolved licenses are a release blocker, **not a justification to skip a private local listening test**.

## Outputs and stop

- `reports/S02A3_SUXIN_MATCHA_LISTENING.md`: detailed pass/fail per actual test and `NOT_RUN` where applicable.
- Record exact tested HEAD and commit, true commands, actual model SHA, WAV SHA and real measurements.
- Update existing PR #7. Do not auto-merge, edit production Sources/eBOOK or Tests, PR #4/#5, or start S02B without the owner's explicit follow-up.
- No paid services, TTS APIs, accounts, model/audio/novel upload to Git, CI artifact or public link.
- Stop at `READY_FOR_AUDIT` with `OWNER_LISTENING_PENDING` until the owner hears the samples.

Acceptance is **genuine Suxin audio** (or a precise, reproducible technical blocker), **same-text private comparison**, honest test environment boundaries and a decision left to the owner. Do not claim that Suxin is bad without generating speech.
