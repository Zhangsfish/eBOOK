# Project Status

- Current owner decision (2026-11-25): two independent conversations share this repository; Suxin ships first and model training targets a later version.
- Current branch/task: `codex/s02b-suxin-ios-integration` / [S02B — Suxin integration](tasks/S02B_SUXIN_IOS_INTEGRATION.md).
- State: **IN_PROGRESS**. Native Mandarin frontend and verified resource preparation implemented;
  author-oracle fixtures contain92 original cases. Native compilation/inference validation pending;
  App voice/player integration, physical-device acceptance and new distribution remain NOT_RUN.
- Coordination: [docs/TTS_WORKSTREAMS.md](docs/TTS_WORKSTREAMS.md). Later-version model work: [PR #11](https://github.com/Zhangsfish/eBOOK/pull/11), `codex/s02a4-teacher-student-tts`; first release does not wait for it.
- Reader baseline: main `83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656`; Suxin experiment frozen at PR #7 `eeee1443c1aac561035cf30590ff323c30ccab8a`.
- Current executor: Windows without Xcode or attached iPhone. Existing approved Python tools,
  ordinary free macOS CI and the owner internal-TestFlight signing bridge are available;
  new native/device results are not claimed until actually observed.
- First delivery uses the existing owner internal-TestFlight path after real integration, validation and independent review. No App Store public release is claimed or newly scheduled.

## Historical S00 status (retained for evidence)

The following snapshot predates the current TTS authorization. PR #5 was subsequently merged at `83fa0d90fd4cd0dbcd791eeb4a3edd53ba985656`; its historical do-not-merge wording is not current PR state. S00 details and earlier test boundaries remain as recorded.

- Project: eBOOK — iOS ebook reader
- Current phase: S00 device preparation follow-up; S01 PR #4 remains READY_FOR_AUDIT.
- Current authorized task on this branch: `tasks/S00_DEVICE_VALIDATION.md`.
- GitHub issue: [#1 — S00 reader foundation](https://github.com/Zhangsfish/eBOOK/issues/1)
- Copy-ready handoff: [tasks/CODEX_HANDOFF_S00.md](tasks/CODEX_HANDOFF_S00.md)
- State: `READY_FOR_AUDIT` — owner feedback 2026-11-25: reopen the TOC at the current
  reading chapter with a selected marker, clear stale search and preserve the
  reading anchor. Follow-up: `reports/S00/toc-current-chapter/`.
  Internal `0.1.0 (39.1)`, implementation `7509547a0b62598097ff5f24ca6eb9611455109c`,
  is Apple VALID/INTERNAL_ONLY and available to the existing owner group. Final
  iOS26.5 and iOS18.5 directory scope each2/2 PASS,0skips; the18.5 first-attempt
  AX timeout remains recorded. These focused runs are not the full28-method suite.
  Previous immersive entry available in internal `0.1.0 (38.1)`,
  tested implementation `326c5438794c76a8978c3cdb049b905ace703f66`. iOS18.5:26/26 PASS;
  iOS26.5:25/26, native Files import UI still FAIL. PR #5 remains draft pending
  independent audit/compatibility triage; do not merge. Owner39.1 feedback pending.
- Implementation branch: `codex/s00-device-validation` (isolated from S01).
- Target: native iOS MVP; EPUB/TXT import, UTF-8/UTF-16/GBK/GB18030 decoding, comfortable reading, persistent positions, and local speech baseline.
- Not authorized: App Store submission, paid services, production backend deployment, account/subscription features, or cloud TTS in S00.

The owner requested parallel iPhone installation on 2026-11-24. This branch
prepares a tested device archive and the separately authorized owner-only
internal-TestFlight installation. Original S00's exclusion applied to that earlier
development task; this follow-up does not authorize public release. S01's review HEAD remains
`3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`; S02A remains in its separate
frozen worktree, and this task does not start S02B.

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

## Owner checks still required
- Update the existing internal TestFlight app to39.1; verify the TOC reveals and
  marks the chapter after reading, closing/reopening and relaunch. Other physical checks
  remain separate in `reports/S00/device-01/DEVICE_CHECKLIST.md`.
- Evaluate premium Mandarin TTS samples and approve any paid API/service in a later phase.

## S00 audit handoff (2026-11-23)
- Complete-suite evidence snapshot: `5714f20c7fce3956b282d04ef10e47d11025b5ae`.
- [Snapshot Xcode run](https://github.com/Zhangsfish/eBOOK/actions/runs/45180857046): Debug/Release simulator builds and 26/26 tests, 0 failures, 0 skips.
- Delivery: [reports/S00_DELIVERY.md](reports/S00_DELIVERY.md); validation: [reports/S00_TEST_RESULTS.md](reports/S00_TEST_RESULTS.md).
- Final delivery HEAD and its own full CI run are recorded in the PR. Later chapter-top/test-navigation fixes are described in reports; do not substitute the snapshot SHA for the final HEAD.
- Physical-device audio/lock-screen/call/Bluetooth validation remains NOT_RUN.
- Repository made public under explicit owner authorization for standard free macOS Actions. No paid runner, merge, release or S01 action.
