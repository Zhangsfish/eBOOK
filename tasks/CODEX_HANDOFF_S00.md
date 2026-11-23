# Codex Handoff — S00

Copy the prompt below into Codex from the local checkout of this repository.

---

You are implementing **only S00 — Reader Foundation** for `Zhangsfish/eBOOK`.

## 1. Synchronize safely

- Run `git status --short --branch` first. Do not discard, reset, stash, or overwrite unrelated local changes.
- Fetch origin.
- Switch to the existing remote branch `codex/s00-reader-foundation`. If the local branch does not exist, create it tracking `origin/codex/s00-reader-foundation`. If it exists, fast-forward only; do not force-push.
- Do not work on `main`.

## 2. Read the source of truth

Read in full:
1. `AGENTS.md`
2. `STATUS.md`
3. `docs/PRODUCT_SPEC.md`
4. `docs/TECHNICAL_PLAN.md`
5. `docs/TEST_DATA.md`
6. `tasks/S00_READER_FOUNDATION.md)
7. GitHub Issue #1: https://github.com/Zhangsfish/eBOOK/issues/1

Follow the current repository documents if this prompt and a document differ. Do not expand scope.

## 3. Implement the vertical slice

Build the native SwiftUI iOS application described by S00:
- Import EPUB and TXT using the iOS document picker / Files.
- Decode UTF-8, UTF-16 LE/BE, GBK, and GB18030 strictly. Never silently display mojibake.
- Parse EPUB metadata, spine, and TOC.
- Render TXT progressively/chunk-wise; do not place a multi-million-character novel in one giant SwiftUI Text view.
- Add conservative TXT chapter-heading heuristics with a fallback when confidence is low.
- Build the library, reader, font/line-spacing controls, light/warm/dark themes, and persistent reading position.
- Add local AVSpeechSynthesizer listening with play/pause/resume, rate, progress, and persisted listening position.
- Handle audio interruptions and background playback where practical.
- Define a provider-neutral seam for future premium TTS. No vendor integration or network synthesis in S00.
- Add tests, README/build instructions, and the S00 delivery/test reports.

## 4. Test data

- Read `docs/TEST_DATA.md`.
- Generate the large original fixture with:
  `python3 scripts/generate_long_gb18030_fixture.py`
- It creates an ignored local file under `.local-test-data/` with 624 synthetic chapters, an afterword, about 2.3 million Unicode characters, and 73,176 lines.
- Use this synthetic fixture for large-file and chapter-navigation performance tests.
- Do not add any complete copyrighted novel or user-imported commercial book to Git, CI, app bundles, logs, screenshots, PR comments, or reports.
- ZIP import is not in S00. EPUB/TXT only.
- Do not send book text to cloud TTS or other external services. Use the local speech adapter.

## 5. Environment and evidence

- Confirm the host is macOS and Xcode is installed before claiming an iOS build.
- Run the actual build and tests. Record exact commands, SDK/simulator destination, pass/fail counts, and any skipped tests.
- If macOS/Xcode is unavailable, stop as `BLOCKED_ENV` with concrete evidence; do not fabricate a build.
- Do not claim background/lock-screen behavior was device-tested unless it was actually tested on a device.

## 6. Git and handoff

- Commit implementation to `codex/s00-reader-foundation`.
- Push the branch and open a PR to `main`.
- Update `reports/S00_DELIVERY.md` and `reports/S00_TEST_RESULTS.md`.
- Include the exact tested HEAD SHA in the PR and reports.
- Set status to `READY_FOR_AUDIT` and STOP.
- Do not merge, do not push to `main`, and do not start S01.

The independent reviewer will audit the diff, implementation, and evidence before authorizing the next step.
