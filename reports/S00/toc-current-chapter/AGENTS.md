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
- .local-test-data/toc-current-chapter/: ignored raw evidence; synthetic books only.

## Handoff
Keep existing iOS26 Files-picker failure explicit; no merge/public release/S02B.
An internal beta may reuse the already-authorized eBOOK signing route described
in ../device-01/INSTALL_PLAN.md, only after actual build/navigation evidence.
Do not claim owner-phone behavior until the owner observes the new build.
