# Project Status

- Project: eBOOK — iOS ebook reader
- Current phase: S00 — Reader foundation
- Current authorized task: `tasks/S00_READER_FOUNDATION.md`
- GitHub issue: [#1 — S00 reader foundation](https://github.com/Zhangsfish/eBOOK/issues/1)
- State: `READY_FOR_CODEX`
- Implementation branch: `codex/s00-reader-foundation`
- Target: native iOS MVP; EPUB/TXT import, including GBK/GB18030 Chinese TXT decoding, basic reading, reading preferences, and a working speech playback baseline.
- Not authorized: App Store submission, paid services, production backend deployment, account/subscription features, or distribution of copyrighted books.

## Latest compatibility finding
A user-provided ZIP was inspected. It contains one file, `绝境黑夜.txt`, which strictly decodes as GBK and identifies the title/author in its header. The chapter headings cover chapters 1–624 and an afterword. The archive itself is a ZIP container; S00 only needs EPUB/TXT import, so the user can extract the TXT in iOS Files before importing it.

This confirms GBK/GB18030 decoding is a required real-world capability. Do not commit or upload the novel/archive to GitHub, CI, fixtures, or app bundles. File inspection does not establish distribution rights or provenance. Synthetic Chinese fixtures must be used for automated tests.

## Handoff protocol
Codex implements only S00, opens a PR to `main`, reports exact tested HEAD SHA and actual build/test results, and stops at `READY_FOR_AUDIT`. ChatGPT independently audits the diff and evidence before any merge or next-stage authorization.

## Owner actions still required later
- Choose/confirm Apple Developer account and signing details when the app reaches device/TestFlight validation.
- Evaluate TTS vendor voice samples and approve any paid API/service.
- Supply an authorized DRM-free test ebook file if testing this specific commercial title is desired.