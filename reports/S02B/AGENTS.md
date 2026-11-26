# S02B integration evidence

Purpose: first-release local Suxin integration on branch codex/s02b-suxin-ios-integration.
Authority: tasks/S02B_SUXIN_IOS_INTEGRATION.md and docs/TTS_WORKSTREAMS.md.
Report: ../S02B_SUXIN_IOS_INTEGRATION.md. evidence/ contains only sanitized small
JSON/log metadata. Raw audio, models and private inputs never enter this folder.
Free isolated CI may export bounded original-fixture UI failure screenshots to
its artifact only; they are downloaded locally, never mixed with user books.
Record exact tested implementation SHA, CI URL and Windows/simulator/iPhone states
separately. First-audible targets are NOT_RUN until actually measured, and a mixer
callback is not a physical acoustic measurement. Independent review precedes the
new internal TestFlight upload; never self-merge or start the training workstream.

## Final audit handoff

Owner follow-up2026-11-26 reopens Files selection repair before the next audit.
Current investigation: DEBUG test-library storage is being aligned with shipping
Application Support instead of the shared Documents tree. This is a hypothesis,
not a proven fix. Constant EBOOK_IMPORT phase/count logs and bounded original UI
failure screenshots distinguish missing picker callbacks from read failures.
Use full42 runs on both existing free standard macOS runners; preserve prior failures.
No new beta before independent review/material clearance. Existing results below
describe8331b9b and its tested ancestors, not the follow-up changes.

Runtime-source follow-up: actual iOS/simulator binaries embed33ca962. Same-commit
LICENSE and complete ThirdPartyNotices were recovered from the binary publisher's
fork at33ca9628233dc8f002435e868d4c2e9f82766ca1, hash checked as data without installs.
The resource inspector/archive driver are being updated to bundle and verify them;
current769e04d CI clones predate these changes and cannot prove their packaging.
Complete license/distribution review is still separate from material presence.

769e04d full18.5 run45754799661 is41/42 again. Phase logs show picker creation
but no selected callback, while fixture/direct imports coordinate and save normally.
Moving the DEBUG library did not resolve the failure. Original UI screenshots
were inspected locally; all three source fixtures remain listed, no App import UI.
Next candidate uses asCopy=false: the existing scoped/coordinated importer owns
the local copy. Real Files entries are explicitly checked enabled in the UI test.
Full42 checks are required again; no success inferred from this code change.
- The chosen Suxin graph is now used by the formal App, with native Swift G2P,
  a single background ORT session, short PCM queue, cache and separate rate.
- Native scope at7c1dba2 is12/12 on both18.5 and26.5, and both unsigned arm64
  archives passed. Full31951f2 runs were41/42; keep those failures in evidence.
- UIKit BookDocumentPicker at3633d42 passed isolated real TXT/EPUB selection and
 cancellation in26.5 (2/2), but18.5 was1/2. Test-only2dbaf25 switches both to List mode.
- Final complete checks:26.5 run45665077113 atf7ae01b and18.5 run45666635333 at2dbaf25.
  Both use App Sources tree36672759f4c470aff8ac41abee2631829017d2e6.
  Both completed41PASS/1FAIL/0SKIP; the failure is still Files selection. Both
  real unsigned Release arm64 archives passed. Keep BLOCKED_QA; isolated success
  did not prove the full-suite entry fixed. No more App changes after2dbaf25.
- READY_FOR_AUDIT with BLOCKED_QA/BLOCKED_ENV/incomplete distribution materials;
  it is not phase acceptance. Physical first-audible/p95/30min/thermal/battery
  remain NOT_RUN. Final mixer probes3.903774/2.218927s and the isolated12-method
  probes3.35–3.60s are not physical-phone latency results. Whole-test-host lifetime
  RSS reached438452224/538345472bytes, not model incremental memory.
- Runtime ZIP has no notices and Microsoft v1.28.2 source/tag queries return404;
  full distribution clearance is incomplete. Do not upload a new beta before review.
- Windows has no Xcode/connected iPhone. No local package/tool installation occurred.
