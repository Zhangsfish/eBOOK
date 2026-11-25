# Current-chapter TOC follow-up

## Purpose and authority
- Owner feedback on 2026-11-25: opening the TOC must reveal the chapter at the
  current reading position every time, without scrolling from the beginning.
- Continue reader branch codex/s00-device-validation / PR #5, base
  4f9175ed6326b95902aceaccf47258771281eac1. Preserve S01 and S02A worktrees.
- This new owner feedback authorizes the narrow reader correction after the
  prior audit handoff. Do not change decoding, persistence formats or speech.

## File map
- Sources/ReaderCore/Models.swift: current TOC entry from absolute reading block.
- Sources/eBOOK/ReaderView.swift: clear stale search, scroll to and mark that row.
- Tests/: actual chapter-boundary and long-book UI regression checks.
- DELIVERY.md: actual tested SHA, CI, internal beta availability and limitations.
- TEST_RESULTS.json: sanitized actual counts/environments/ZIP verification, with
  initial failures preserved and focused reruns recorded separately.
- evidence/: unmodified original-text simulator screenshots and their SHA256 /
  exact source/run provenance. Never add owner book images or Apple identities.
- scripts/ci_xcode.sh + existing workflows: optional reader-toc scope runs the
  exact boundary + dedicated live-chapter/search/relaunch UI methods with count2/no skips;
  original all/native-picker modes remain. This avoids rerunning unrelated tests
  after the first run exposed a localized-number parsing error in the new helper.
- The dedicated case crosses a chapter by genuine reader swipes after a TOC
  jump, so retaining the previous selected chapter cannot falsely pass it.
- iOS18.5 exposed an auto-collapsing search drawer after deep TOC scrolling;
  navigationBarDrawer(displayMode:.always) preserves the search affordance.
- .local-test-data/toc-current-chapter/: ignored raw evidence; synthetic books only.

## Handoff
Keep existing iOS26 Files-picker failure explicit; no merge/public release/S02B.
An internal beta may reuse the already-authorized eBOOK signing route described
in ../device-01/INSTALL_PLAN.md, only after actual build/navigation evidence.
Do not claim owner-phone behavior until the owner observes the new build.

## Latest measured checkpoint
- Final7509547a0b62598097ff5f24ca6eb9611455109c: run45548099346(Xcode26/iOS26.5)
  passed2/2,0skips, builds/archive and actual bounded renderer metrics. Three
  unmodified750 screenshots are in evidence/ with SHA256 provenance.
- 45548105689(Xcode16.4/iOS18.5) attempt1:1/2, AX snapshot query timeout before
  opening the book, no directory assertions reached. Same-source attempt2
  passed2/2 with0fail/0skip, Debug/Release builds and bounded renderer checks.
  Attempt1 remains recorded; cause is undetermined. Neither focused pass is a
  full28-method regression. Final18.5 ZIP digest6a5c1ea2... matches the server.
- Internal0.1.0(39.1) is available: helper0be62cf0a51a5dfc0f8a271b95c2ae9e31c22ded,
  upload45550231458, exact reader7509547. Apple accepted05:00:45UTC, VALID and
  existing owner-group linkage verified05:02:25UTC. Guard checkedINTERNAL_ONLY.
  No retained signed IPA/hash claimed. Owner update/TOC feedback is pending.

- State: READY_FOR_AUDIT. No runtime/test/CI/project changes after7509547;
  final delivery commit contains documentation and sanitized screenshot evidence only.
