# S02B integration evidence

Purpose: first-release local Suxin integration and owner-requested Files follow-up
on codex/s02b-suxin-ios-integration / PR12. Worktree E:/myself/eBOOK-s02b.
Authority: tasks/S02B_SUXIN_IOS_INTEGRATION.md and docs/TTS_WORKSTREAMS.md.
Current state: IN_PROGRESS until the final complete two-runtime checks finish.
Do not merge, sign/upload a new beta before independent review, or edit PR7/11.

## Current source and actual results

- Formal App Sources tree6d9339b31da7acd614971037c2e9151e493bdc48, frozen since
  16fe15da6bcd7431a8a162fd65ca77ce8da6ff4d. Later changes only adjust test/CI/docs.
- 16fe15d /26.5 run45757095612: complete42PASS/0FAIL/0SKIP; actual native Suxin,
  long-reader and real Files checks pass, unsigned arm64 Release archive pass.
- 3bfc352 /18.5 run45761286868: complete41PASS/1FilesFAIL/0SKIP; TOC, actual
  native Suxin, other reader tests and arm64 archive pass. Keep the failed attempt.
- 16fe15d /18.5 run45757099825: TIMEOUT with partial40PASS/1FAIL/1TOCunfinished;
  no final xcresult summary/archive. Never call this a completed42-method run.
- fba530b3749b1ea94db44fac9b4c01bc9cb81283 /18.5 run45767237191: focused
  actual external Files import/cancel2PASS/0FAIL/0SKIP. Logs show two selected
  callbacks and saved books1/2. Actual arm64 archive92,986,336bytes,6 model
  resources and2 exact-source runtime notices verified. This scope did not run TTS.
- Final full42 runs at7ff918a1c02f730bf37d351821b37dc79709c2e3 are pending:
  iOS18.5/45769244490 and iOS26.5/45769249483. Do not infer their results yet.

## Files investigation and retained failures

Current App uses UIDocumentPicker asCopy=false; LibraryModel reads the scoped URL
with NSFileCoordinator and BookImporter makes a bounded App-private copy. DEBUG
library uses Application Support like the shipping app. Constant EBOOK_IMPORT logs
contain only phases/counts/codes, never book names/paths/body.

Older probes selected source fixtures from the reader's own shared Documents tree.
18.5 labels were wide; leading-coordinate selection did not fix that experiment.
The current test uses the actual observed system FileProvider.LocalStorage group,
prepares only original TXT/EPUB under File Provider Storage/eBOOK Import Test,
and navigates/selects through real native Files UI. No reader-library injection.
Observed18.5 title is a menu button, not the nav-bar identifier; wait for the actual
My iPhone back button and tap it before choosing the external folder.

Stock Files independent simctl launch timed out30s even in the successful fba
picker run. This does not establish an Apple defect or block all native selection.
6017303 probe failed before App compilation;4a5b716 failed in test navigation,
not after external file selection. Preserve both rather than relabeling them PASS.
Older8331b9b two-runtime41/42 delivery remains a historical section in the report.

## Resource and review boundaries

Actual iOS/simulator ORT slices embed33ca962. Same complete source commit
33ca9628233dc8f002435e868d4c2e9f82766ca1 in the publisher fork provides
Microsoft LICENSE and complete ThirdPartyNotices. Preparation hash-pins both;
actual archives on18.5 and26.5 verify their bundled bytes. Original ZIP0notices
and old404 queries remain historical evidence. Material recovery is not a
reproduced binary build, exhaustive dependency BOM or independent legal clearance.
Do not edit any bundle-producing NOTICE/manifest/prepare/inspector resources
without rerunning the actual archive checks.

## Evidence map and privacy

- ../S02B_SUXIN_IOS_INTEGRATION.md: canonical report, old failures retained.
- FILES_IMPORT_FOLLOWUP.md: current selection/CI follow-up.
- DEVICE_CHECKLIST.md: pending phone tests, not test results.
- evidence/: only sanitized small JSON/log metadata, exact test SHA and CI URL.
- ../../.local-test-data/s02b/files-followup/: ignored raw CI downloads and original
  diagnostic PNGs. Do not add binaries/audio/private books to Git or public artifacts.
CI may export only bounded original-fixture failure PNGs, never user books.

## Remaining phone validation

Physical new-process first sound, warm/jump p95,1.0x/1.5x each30min, lockscreen,
interruptions/headphones/Bluetooth, thermal/battery remain NOT_RUN. Mixer callback
is not acoustic latency; lifetime test-host RSS is not model incremental memory.
Old installed39.1 is Apple-only. No new signed/TestFlight build is claimed.
Windows has no Xcode or attached iPhone. Reuse existing Python/gh/Pillow and free
standard public macOS CI; no local install occurred in this follow-up.
