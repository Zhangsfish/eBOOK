# Project Status

- Project: eBOOK — iOS ebook reader
- Current phase: S00 — Reader foundation
- Current authorized task: `tasks/S00_READER_FOUNDATION.md`
- GitHub issue: [#1 — S00 reader foundation](https://github.com/Zhangsfish/eBOOK/issues/1)
- Copy-ready handoff: [tasks/CODEX_HANDOFF_S00.md](tasks/CODEX_HANDOFF_S00.md)
- State: `IN_PROGRESS` — S00 implementation and real Xcode validation underway.
- Implementation branch: `codex/s00-reader-foundation`
- Target: native iOS MVP; EPUB/TXT import, UTF-8/UTF-16/GBK/GB18030 decoding, comfortable reading, persistent positions, and local speech baseline.
- Not authorized: App Store submission, paid services, production backend deployment, account/subscription features, or cloud TTS in S00.

## Measured compatibility profile

The ZIP attachment supplied in the planning conversation was inspected in place. It has not been added to this repository.

- ZIP size: 2,237,474 bytes.
- One inner file: `绝境黑夜.txt`.
- Inner TXT size: 4,439,158 bytes.
- Strict decoding succeeds with both GBK and GB18030.
- Decoded length: 2,301,482 Unicode characters including CRLF line endings; 73,176 lines.
- Header metadata identifies `绝境黑夜` by `滚开` and states progress through chapter 624 plus an afterword.
- Heading formats are heterogeneous; a single `^第N章` expression does not identify every chapter heading.
- ZIP is only a container. S00 supports EPUB/TXT; ZIP import is not required.

These measurements are recorded as a non-text compatibility profile only. The full archive and novel text must not be committed, uploaded, bundled, placed in CI, or copied into reports/logs. Use the reproducible synthetic fixture described in `docs/TEST_DATA.md` for automated and performance testing.

## Handoff protocol
Codex implements only S00, opens a PR to `main`, reports exact tested HEAD SHA and actual build/test results, and stops at `READY_FOR_AUDIT`. ChatGPT independently audits the diff and evidence before any merge or next-stage authorization.

## Owner actions still required later
- Choose/confirm Apple Developer account and signing details when the app reaches device/TestFlight validation.
- Evaluate premium Mandarin TTS samples and approve any paid API/service in a later phase.
