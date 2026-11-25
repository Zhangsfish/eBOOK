# S02B integration evidence

Purpose: first-release local Suxin integration on branch codex/s02b-suxin-ios-integration.
Authority: tasks/S02B_SUXIN_IOS_INTEGRATION.md and docs/TTS_WORKSTREAMS.md.
Report: ../S02B_SUXIN_IOS_INTEGRATION.md. evidence/ contains only sanitized small
JSON/log metadata. Raw audio, models and private inputs never enter this folder.
Record exact tested implementation SHA, CI URL and Windows/simulator/iPhone states
separately. First-audible targets are NOT_RUN until actually measured, and a mixer
callback is not a physical acoustic measurement. Independent review precedes the
new internal TestFlight upload; never self-merge or start the training workstream.

## Final audit handoff
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
