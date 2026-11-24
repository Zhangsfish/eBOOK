# Codex handoff — S02A (free on-device Mandarin TTS)

You are working **only** on `Zhangsfish/eBOOK` Issue #6, native iOS feasibility for Kokoro Chinese + sherpa-onnx.

1. Check `git status --short --branch`. Preserve unrelated work. Fetch origin. Switch/track `codex/s02a-kokoro-ios-spike` and fast-forward only. Do not work on main.
2. Read `AGENTS.md`, `docs/PRODUCT_STRATEGY_ZERO_COST_TTS.md`, `docs/PRODUCT_SPEC.md`, `tasks/S02A_KOKORO_IOS_SPIKE.md`, and https://github.com/Zhangsfish/eBOOK/issues/6. This new task is authoritative; S01 PR #4 and Reader/UI PR #5 are open, so do not touch their files or branches.
3. The user-facing goal is 4 FREE voices: Apple Chinese system fallback plus 2 female and 1 male Chinese Kokoro voices **from one shared model**, no subscription, no API key, no paid request.
4. Implement only `tools/local-tts-spike/` and `reports/S02A_LOCAL_TTS_FEASIBILITY.md`: reproduce the upstream sherpa-onnx Swift/iOS Kokoro v1.1 Chinese INT8 runtime, pin hashes and upstream versions, generate original Chinese sample WAVs on the local machine and, critically, **perform actual Chinese speech synthesis in an iOS simulator** if supported.
5. Initial trial IDs: zf_001=sid3, zf_002=sid4, zm_009=sid58. They are unreviewed trial voices, not final pleasant-voice claims. Produce short original narration/dialogue/number samples with a local anonymous listening index. Assets/WAVs stay under ignored `.local-test-data/`; never upload them to the repo or GitHub Actions.
6. Measure actual downloaded/unpacked model bytes, startup, first-chunk latency, generation real-time factor, peak RSS, and bounded multi-chunk generation for a 10–15-minute listening workflow. Distinguish host desktop vs simulator vs device. No physical-device/lock-screen claims without actual tests.
7. Review the license and redistribution notices for all model/runtime/frontend files; do not assume the upstream weight license covers every bundled dictionary/native dependency.
8. Do not edit existing iOS Sources, Xcode project, tests, S01 voice lab, UI PR, workflows or main. No production integration or cloud APIs, no paid services or third-party accounts.
9. Finish with a PR to main, true build/inference evidence, exact tested HEAD SHA, clear GO/BLOCKED/NO-GO finding, and READY_FOR_AUDIT. Do not merge or begin S02B.

If available host is Windows, perform desktop validation there and use the existing authorized public-repository macOS GitHub runner for native iOS simulator verification, without enabling a paid runner. If a real iOS runtime/model load cannot be demonstrated, stop with explicit BLOCKED_IOS_RUNTIME rather than representing desktop success as iOS success.
