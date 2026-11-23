# Project Status

- Project: eBOOK — iOS ebook reader
- S00: **MERGED** into main via PR #2.
- S00 merge commit: adc9f340a2ff427b30cddce33ad8a4d9efdac55a.
- S00 tested implementation HEAD: 672d36acc78fecc95183759d2ae590f8978553d9.
- S00 final-HEAD Xcode Actions: https://github.com/Zhangsfish/eBOOK/actions/runs/45188325769 — success, 26/26 simulator tests, Debug and Release simulator builds passed.
- Current phase: S01 — Mandarin TTS Voice Lab.
- Current authorized task: tasks/S01_TTS_VOICE_LAB.md.
- GitHub Issue: https://github.com/Zhangsfish/eBOOK/issues/3.
- Copy-ready Codex handoff: tasks/CODEX_HANDOFF_S01.md.
- Branch: codex/s01-tts-voice-lab.
- State: READY_FOR_AUDIT — local S01 implementation/evidence prepared; independent review pending. Final HEAD/CI results are recorded in the PR.
- S01 purpose: build an offline-first local audition harness and compare Mandarin TTS candidates using original synthetic text.
- S01 does NOT integrate cloud TTS into the app, deploy a backend, or authorize live API calls or spending.

## Product state

The current main branch contains the native SwiftUI reader:
- iOS 17+; EPUB/TXT import.
- UTF-8, UTF-16, GBK and GB18030 TXT decoding.
- EPUB navigation, searchable TOC, font/line spacing and light/warm/dark themes.
- Separate persistent reading and listening positions.
- Apple AVSpeechSynthesizer local speech fallback.
- Long-form text stored and rendered in bounded blocks/windows.

Physical-device validation remains outstanding: signed install, background/lock-screen endurance, calls, Bluetooth/headset controls, iOS 17 runtime and manual accessibility review.

## S01 source of truth

- Task: tasks/S01_TTS_VOICE_LAB.md.
- GitHub Issue: https://github.com/Zhangsfish/eBOOK/issues/3.
- Handoff: tasks/CODEX_HANDOFF_S01.md.
- Candidate and evaluation protocol: docs/TTS_VOICE_LAB.md.
- Provider decision record: docs/S01_PROVIDER_DECISION.md.
- S00 product and technical baseline: docs/PRODUCT_SPEC.md and docs/TECHNICAL_PLAN.md.

## S01 spend and privacy gates

- No provider has been selected.
- No live API calls, paid usage, account creation, voice cloning or credential requests are authorized in S01.
- Use original synthetic Mandarin samples only. Never send a commercial novel or user-imported ebook to a vendor.
- Secrets stay in local environment variables; no keys in GitHub, app bundle, Xcode settings, logs or screenshots.
- Audio audition outputs stay under ignored .local-test-data/tts-auditions/.
- S01 exits with a blind listening page, score sheet, provider-specific cost accounting and a report. The owner listens and chooses before S02 integration.

## Historical compatibility profile

A ZIP attachment supplied during planning was inspected in place and not added to the repository:
- ZIP size: 2,237,474 bytes; one inner TXT.
- Inner TXT size: 4,439,158 bytes.
- Strict decoding succeeded as GBK and GB18030.
- Decoded length: 2,301,482 Unicode characters including CRLF; 73,176 lines.
- Header metadata identified 绝境黑夜 by 滚开, chapter 624 plus afterword.
- Chapter-heading styles were heterogeneous.

These non-text measurements are retained only as a compatibility profile. The archive and novel text are not repository test assets. S00 used a reproducible synthetic fixture.

## Collaboration protocol

Codex implements only the task marked READY on its task-specific branch, opens a PR to main, reports exact tested HEAD SHA and actual results, then stops at READY_FOR_AUDIT. ChatGPT independently reviews the diff and evidence. No self-approval, direct push to main or automatic merge.

S00 Issue #1 is complete and closed. S01 is the only currently authorized development task.

## S01 audit handoff

- Workbench: [tools/tts-lab/README.md](tools/tts-lab/README.md).
- API contract sources: [docs/TTS_PROVIDER_API_CONTRACTS.md](docs/TTS_PROVIDER_API_CONTRACTS.md).
- Results and limits: [reports/S01_TTS_EVALUATION.md](reports/S01_TTS_EVALUATION.md).
- Local checks: 38 offline unit tests; default/all-provider Dry Run; browser A/B
  checks at three widths; deterministic Xcode-project check. No live provider
  request, real voice listening score or paid usage.
- The final delivery HEAD and actual free-macOS iOS regression run are recorded
  in the PR. S00 app sources and playback behavior remain unchanged.
- Provider choice remains OPEN. No merge, cloud integration, backend or S02.
