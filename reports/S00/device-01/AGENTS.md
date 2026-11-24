# eBOOK physical-device preparation

## Authority and scope
- The owner requested parallel installation/device testing on 2026-11-24.
- Base: main `adc9f340a2ff427b30cddce33ad8a4d9efdac55a`.
- Use `codex/s00-device-validation` in the separate device worktree.
- Preserve S01 PR #4 and its reviewed HEAD `3bfb4429fe7a42e50df62f4857bcb9909bf00ab3`.
- This follow-up prepares the existing reader for owner installation; it is not S02.
- Original S00 excluded TestFlight within that development task. The owner's
  later instruction to install/test on the iPhone authorizes this separate
  internal-TestFlight follow-up using the existing signing route. Do not ask
  again for routine packaging/signing/installation steps already covered by it.
- The owner completes Apple login/verification directly in the official UI.
- No App Review submission, public release, new paid service, cloud TTS or merge.
- New owner feedback on installed35.1: local TXT import/read works well; make the
  permanent bottom speech controls appear only when needed. ReaderView presentation
  and its meaningful native UI regression are authorized; keep engines unchanged.
- Do not acquire or request the private imported book. Record only the owner's
  non-textual import/read observation; no book content in reports/screenshots.

## File map and provenance
- `DEVICE_CHECKLIST.md`: owner checks, initially NOT_RUN.
- `DELIVERY.md`: exact implementation/build/installation state and blockers.
- `TEST_RESULTS.json`: per-run SHA, real outcomes and physical-owner observations;
  distinguish the signed build source from the final documentation-only PR head.
- `scripts/ci_device.sh`: real unsigned iPhone archive and package inspection.
- `.github/workflows/s00-device.yml`: standard public macOS runner; no secrets.
- `Sources/eBOOK/Assets.xcassets`: original geometric book icon, no external art.
- `Tests/UITests/ReaderUITests.swift`: retain native picker flow/assertions; fall
  back to the visible filename when iOS 26's thumbnail tap leaves the picker open.
- `.local-test-data/device-01/`: ignored private local outputs; no Apple secrets
  or private device identifiers in this folder, Git, logs or screenshots.

## Handoff
Keep compile, unsigned archive, signing, upload acceptance, Apple processing,
owner installation and physical behavior as separate evidence states.
Only owner-observed device results can change checklist rows from NOT_RUN.

## Current installed beta
- eBOOK `0.1.0 (35.1)`, source `1e556ae1622b4d56fa3c0c9e05ca0a14877073ac`.
- Existing-repository helper `68ec0136774cb147004887ee79e0c1d099c41c01`, successful
  upload/status run 45325301937; Apple VALID and Internal Only read back in UI.
- Owner iPhone group: automatic distribution disabled, one manually added build,
  only the existing account-holder invited. No private tester email in reports.
- Owner reported installation/launch and private TXT import/read success. EPUB,
  locked10-minute speech, restore, memory, calls and accessibility remain pending.
- The next beta must include the explicitly requested on-demand speech panel.
