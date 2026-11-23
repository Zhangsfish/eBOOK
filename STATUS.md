# Project Status

- Project: eBOOK — iOS ebook reader
- Current phase: S00 — Reader foundation
- Current authorized task: `tasks/S00_READER_FOUNDATION.md`
- State: `READY_FOR_CODEX`
- Implementation branch: `codex/s00-reader-foundation`
- Target: native iOS MVP foundation; EPUB/TXT import, basic reading, reading preferences, and a working speech playback baseline.
- Not authorized: App Store submission, paid services, production backend deployment, account/subscription features, or distribution of copyrighted books.

## Handoff protocol
Codex implements only S00, opens a PR to `main`, reports exact tested HEAD SHA and actual build/test results, and stops at `READY_FOR_AUDIT`. ChatGPT independently audits the diff and evidence before any merge or next-stage authorization.

## Owner actions still required later
- Choose/confirm Apple Developer account and signing details when the app reaches device/TestFlight validation.
- Evaluate TTS vendor voice samples and approve any paid API/service.
- Supply authorized test ebook files if testing a specific commercial title is desired.