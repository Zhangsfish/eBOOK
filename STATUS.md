# Project Status

- Project: eBOOK — iOS ebook reader
- Current phase: S00 — Reader foundation
- Current authorized task: `tasks/S00_READER_FOUNDATION.md`
- GitHub issue: [#1 — S00 reader foundation](https://github.com/Zhangsfish/eBOOK/issues/1)
- State: `READY_FOR_CODEX`
- Implementation branch: `codex/s00-reader-foundation`
- Target: native iOS MVP foundation; EPUB/TXT import, basic reading, reading preferences, and a working speech playback baseline.
- Not authorized: App Store submission, paid services, production backend deployment, account/subscription features, or distribution of copyrighted books.

## Handoff protocol
Codex implements only S00, opens a PR to `main`, reports exact tested HEAD SHA and actual build/test results, and stops at `READY_FOR_AUDIT`. ChatGPT independently audits the diff and evidence before any merge or next-stage authorization.

## Content test case
`绝境黑夜` by 滚开 is the target long-form Chinese-fiction compatibility case. The work is listed on Qidian (book ID 1040146263); Shuqi's listing states that the digital rights are provided by Yuewen and licensed to Shuqi. Neither listing establishes that a DRM-free EPUB/TXT export is available. Do not scrape or bypass the official apps' access controls. Use a lawfully obtained, user-exportable file only; otherwise validate with synthetic Chinese fixture text.

## Owner actions still required later
- Choose/confirm Apple Developer account and signing details when the app reaches device/TestFlight validation.
- Evaluate TTS vendor voice samples and approve any paid API/service.
- Supply an authorized DRM-free test ebook file if testing this specific commercial title is desired.
