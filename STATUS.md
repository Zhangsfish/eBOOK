# Project Status

## Current owner request — reader controls, tutorial and feedback (2026-11-27)

- **IN_PROGRESS**: [task](tasks/S02B_READER_HELP.md), existing PR12/branch. Compact bottom icon row and smaller progress thumb, local skippable/replayable animated tutorial, bookshelf feedback with the existing approved contact.
- Owner explicitly requests direct internal phone testing after focused real validation, without another web review for this scope. Preserve Suxin and existing privacy/progress; no merge/public release or other workstream changes.
- 48.1 and all earlier evidence below remain retained. New source/build/device acceptance is not yet claimed. [Current scope memory](reports/S02B/reader-help/AGENTS.md)

## Current delivery — TestFlight 48.1, waiting for phone feedback (2026-11-27)

- **APPROVED_FOR_OWNER_BETA** for owner-requested copy and side taps. [Independent review](reports/S02B/owner-polish/INDEPENDENT_REVIEW.md) · [Delivery evidence](reports/S02B/owner-polish/DELIVERY.md).
- Approved/tested `03fe0237462f0af0595d47c455c7e5756d6cbd97`; delivery2d3be5e has identical eight build inputs. Independent review verified actual18.5/26.5 logs and artifacts: each10PASS/0FAIL/0SKIP, unsigned arm64 and6+2 resources. No App blocker identified for owner trial.
- **WAITING_OWNER_FEEDBACK**. The approved reader is available as **0.1.0 (48.1)**. Apple read back `VALID`, `INTERNAL_ONLY`, unexpired, existing Owner iPhone linkage and `IN_BETA_TESTING` at 19:38:08 Beijing. [Phone delivery](reports/S02B/owner-polish/PHONE_DELIVERY.md)
- Bridge `e0a122b499ef417fba032e58cb1181594634a08a` verified matching executable digests with and without a link map, then the existing static-link and 6+2 resource checks. [Actual upload run 45991125943](https://github.com/Zhangsfish/lecture-asset/actions/runs/45991125943)
- App work is frozen pending actual 48.1 phone feedback. The owner liked the voice on 47.1. Device experience on 48.1 is pending.

## Delivered owner trial — retained evidence

- Decision: **APPROVED_FOR_OWNER_BETA**. R1–R3 CLOSED; reviewed reader `6469489062e6b91d743295cc2c08320334dbbf17`, delivery `ca640cd1f982b71927c7db2138150ff657cfdb11`. Actual iOS18.5 and26.5 each55/55; original device entry/6+2 resources verified.
- **WAITING_OWNER_FEEDBACK:** [owner trial delivery](reports/S02B/OWNER_PHONE_TRIAL.md), **0.1.0（47.1）**. [Independent review and stop rules](reports/S02B/REVIEW_AND_OWNER_TRIAL_20261127.md). Feature development remains frozen.
- Existing eBOOK-only bridge `a866cd83c342e3652555080de949ca47ac1349e0`, [actual run45933165856](https://github.com/Zhangsfish/lecture-asset/actions/runs/45933165856), delivered the approved reader. Bounded packaging removes only a proven-unused framework; the compiled executable and6+2 resources remain intact.
- `TESTFLIGHT_AVAILABLE=YES`: Apple read back47.1 VALID/INTERNAL_ONLY/unexpired, the existing Owner iPhone group and IN_BETA_TESTING at2026-11-27 11:21:56 Beijing.39.1 retained; owner installation/upgrade is still NOT_RUN, not inferred from availability.
- Owner's later qualitative voice feedback is positive. Latency/background/thermal/upgrade measurements remain unreported; do not promote the sound comment into those results.
- After owner accepts core use, end this MVP implementation round and freeze the usable version. Only actual owner-reported/core defects reopen fixes. No extra feature, model switch or generic optimization.
- PR #11 / #7 / Android remain separate. No self-merge or public App Store release.

## Previous delivery snapshot (retained; current READY task above supersedes its stop/freeze wording)

- Current owner decision (2026-11-25): two independent conversations share this repository; Suxin ships first and model training targets a later version.
- Current branch/task: `codex/s02b-suxin-ios-integration` / [S02B — Suxin integration](tasks/S02B_SUXIN_IOS_INTEGRATION.md).
- State: **READY_FOR_AUDIT — Files verified; remaining BLOCKED_QA / physical BLOCKED_ENV**.
  App Sources `6d9339b31da7acd614971037c2e9151e493bdc48`, frozen since16fe15d.
  Complete7ff918a results:18.5/45769244490 is42PASS/0FAIL/0SKIP;
  26.5/45769249483 is41PASS/1FAIL/0SKIP. Real TXT/EPUB selection/cancel, all six UI,
  native Suxin12 and long-reader checks pass in both complete runs. Actual unsigned
  arm64 Release archives verify6 model files and2 exact-source runtime notices.
  The26.5 failure is Apple speech sawRange at line184 after finished was observed.
  One clean recheck565bae0/45771793206 ended with6 UI PASS plus1 EBookTests
  startup error record (signal abrt before XCTest connection); unit/native methods
  and archive NOT_RUN in that attempt. This is not a completed42-method suite or
  a successful Apple-callback recheck. No further rerun; unique cause remains unknown.
  Preserve all prior failures and the18.5 partial timeout. Independent distribution
  review and physical first sound/p95/long listening/thermal/battery remain pending.
  No new signed/TestFlight build; old39.1 is unchanged. Stop for independent audit,
  do not self-merge, upload before review, or start another feature/model task.
  [Files follow-up](reports/S02B/FILES_IMPORT_FOLLOWUP.md) and
  [canonical report](reports/S02B_SUXIN_IOS_INTEGRATION.md).
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
